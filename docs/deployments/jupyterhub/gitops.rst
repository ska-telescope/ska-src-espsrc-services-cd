.. _jupyterlab-gitops: 

JupyterHub - GitOps
=================================

.. tip::
    
    espSRC JupyteHub service endpoint: https://notebook.espsrc.iaa.csic.es 


.. note ::
    Kubernetes Server Version: v1.30.6+k3s1
    JupyterHub Version: 3.1.0
    Flux version: 

JupyterHub is a powerful multi-user platform that provides Jupyter notebook environments 
to various users, ideal for education, research, and collaborative projects. 
Deploying JupyterHub on a Kubernetes cluster enables seamless scalability and centralized 
resource management, allowing multiple users to access individual, isolated notebook 
instances through a single, unified interface.

This GitOps-based installation automates the deployment of this type of services, through 
the configuration of a repository where the application deployment files are located.

Prerequisites
-------------

Kubernetes Cluster
^^^^^^^^^^^^^^^^^^

Ensure you have a running Kubernetes cluster with at least the next versions:

.. note ::

    Client Version: v1.30.6+k3s1
    Kustomize Version: v5.0.4-0.20230601165947-6ce0bf390ce3
    Server Version: v1.30.6+k3s1

Helm
^^^^ 

Install Helm for deploying this JupyterHub Chart

.. code-block:: bash

   curl -fsSL -o get_helm.sh https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3
   chmod 700 get_helm.sh
   ./get_helm.sh


Vault and External Secrets
^^^^^^^^^^^^^^^^^^^^^^^^^^

Ensure Vault is configured, with necessary secrets accessible in External Secrets.

Storage backend
^^^^^^^^^^^^^^^

To support the Kubernetes cluster it is necessary to have a storage backend through a StorageClass. 
In our deployment we have chosen to provide the cluster with shared storage based on CephFS, so 
each node has mounted by default the /mnt/k8s-shared/ directory. 

The configuration and mounting of this directory is automatic at node instantiation time. 
However, to do it manually, we apply the following command on each node:

.. code-block:: bash
    
    sudo mount -t ceph 172.16.5.115:6789,172.16.5.116:6789,172.16.5.117:6789:/volumes/_nogroup/0f611fdf-4c5a-400b-b45a-95be2481333b/6e3395d7-7a17-4e69-899b-370ef1ba42fe \
                  /mnt/k8s-shared/ \
                  -o name=spsrc-k8-cluster00 \
                  -o secretfile=/etc/ceph/ceph.client.k8s-shared.secret

.. important ::

Previously to do this step you must have created the CephFS storage with the following procedure for a 20TB storage folder:

``openstack share create --share-type cephfstype --name k8s-shared cephfs 20480``


StorageClass
^^^^^^^^^^^^

To manage the storage space of the cluster, CephFS has been chosen, so that each node has a shared directory 
where all the Persisten Volumes (PV) that the applications deploy will be stored. To do this, the following 
configurations will be necessary:

Install the corresponding StorageClass: 

.. code-block:: bash
    
    kubectl apply -f https://raw.githubusercontent.com/rancher/local-path-provisioner/master/deploy/local-path-storage.yaml

Then include the folder of the mounted CephFS folder:

.. code-block:: bash
    
     kubectl edit configmap local-path-config -n local-path-storage

Change the path with ``paths":["/mnt/k8s-shared/"]`` where our CephFS folder is set:

.. code-block:: bash

    apiVersion: v1
    data:
    config.json: |-
        {
                "nodePathMap":[
                {
                        "node":"DEFAULT_PATH_FOR_NON_LISTED_NODES",
                        "paths":["/mnt/k8s-shared/"]
                }
                ]
            }
    ...



Kustomization files
-------------------

All the files for this FluxCD kustomization are here:

.. code-block:: bash
    
    ~/apps/jupyterhub/gitops

Clone this repo to modify/updgrade them and FluxCD will do the rest. See the structure for this JupyterHub in the following subsection.

Structure of the deployment for JupyterHub
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    kustomization.yaml
      - service/
        - kustomisation.yaml # Index for files to ve included within the kustomisation
        - ServiceAccount.yaml # Creates the Service Account for this JupyterHub deployment.
        - SecretStore.yaml # Point to the Vault Secret Store and the Role for JupyterHub.
        - ExternalSecret.yaml # Secrets to be used for the JupyterHub deployment.
        - helmrepository.yaml # Repository of the JupyterChart.
        - helmrelease.yaml # Repository of the Helm Chart release and version.
        - values.yaml # Values files that will be injected combined with ExternalSecret secrets.

Secrets creation
^^^^^^^^^^^^^^^^

Add the next:

.. code-block:: bash
    
    kubectl exec -it vault-0 -n vault -- /bin/sh

    vi jupyter_policy.hcl
    ## Add the next:

    path "*" {
        capabilities = ["read"]
    }

Then apply this policy:

.. code-block:: bash
    
    vault policy write jupyter-policy jupyter_policy.hcl

Add the role: 

.. code-block:: bash
    kubectl exec -it vault-0 -n vault -- /bin/sh

    vault write auth/kubernetes/role/jupyterhub bound_service_account_names=jupyterhub  bound_service_account_namespaces=jupyterhub-test policies=jupyter-policy ttl=24h

Create the next secrets in Vault:

.. code-block:: bash

    kubectl exec -it vault-0 -n vault -- /bin/sh

    vault kv put app/jupyter client-secret="<client-secret here>" \ 
        client-id="<client-id here>" token="<token here>"


Secrets injection
^^^^^^^^^^^^^^^^^

JupyterHub with OAuth authentication needs CLIENT-ID and CLIENT-SECRET from the SKAO-IAM and a TOKEN for the proxy parameter.
The next code (``service/ExternalSecret.yaml``) contains the secrets we are getting to inject them in this deployment. 

.. note::

    Note ``secretKey: CLIENT-ID`` is the name within the deployment. ``remoteRef.key: app/data/jupyter`` is the path within Vault and ``property: client-id`` is the key create in the previous step.

.. code-block:: bash

    ...
    spec:
    refreshInterval: "15s" 
    secretStoreRef:
        name: vault-secret-store 
        kind: SecretStore
    target:
        name: jupyterhub-secrets
        creationPolicy: Owner 
    data:
        - secretKey: CLIENT-ID 
        remoteRef:
            key: app/data/jupyter 
            property: client-id 
        - secretKey: CLIENT-SECRET 
        remoteRef:
            key: app/data/jupyter 
            property: client-secret 
        - secretKey: TOKEN 
        remoteRef:
            key: app/data/jupyter 
            property: token 

Then in SecretStore (``service/SecretStore.yaml``) we include the specific role and service account reference created previously:

.. code-block:: bash
    ...
     auth:
       kubernetes:
         mountPath: "kubernetes"
         role: "jupyterhub" 
         serviceAccountRef:
           name: "jupyterhub"


Values injection
^^^^^^^^^^^^^^^^

Values for this deployment are placed in ``service/values.yaml``. This is the main values file and 
to mix this values files with other value, for example the Secrets values, you have to modify ``service/helmrelease.yaml`` 
and to include the values and the path for these values following the same structure the ``values.yaml`` file:

.. code-block:: bash
  
  ...
  valuesFrom:
    - kind: Secret
      name: jupyterhub-secrets
      valuesKey: TOKEN
      targetPath: proxy.secretToken
      optional: false
    - kind: Secret
      name: jupyterhub-secrets
      valuesKey: CLIENT-ID
      targetPath: hub.config.GenericOAuthenticator.client_id
      optional: false
    - kind: Secret
      name: jupyterhub-secrets
      valuesKey: CLIENT-SECRET
      targetPath: hub.config.GenericOAuthenticator.client_secret
      optional: false
    - kind: ConfigMap
      name: jupyterhub-values

For example ``TOKEN`` is the name of the variable with a Secret defined 
in ``service/ExternalSecret.yaml``. Then ``targetPath: proxy.secretToken`` is where 
the variable will be inyected, in this case ``proxy.secretToken`` that will be the same as:

.. code-block:: bash

    ...
    proxy:
        secretToken: <injected value>
    ... 

FluxCD
------
Once all these steps are ready, is time to add the repo folder to be managed by FluxCD.
Run the flux bootstrap aganist the apps included within the ``/apps`` folder in ``ska-telescope/src/deployments/espsrc/ska-src-espsrc-services-cd`` repository.

.. code:: bash
    
    flux bootstrap gitlab   \ 
        --owner=ska-telescope/src/deployments/espsrc   \ 
        --repository=ska-src-espsrc-services-cd   --branch=main   \ 
        --path=./apps   --personal   --deploy-token-auth

Check the overall status of the JupyterHub release and kustomisation:

.. code:: bash

    flux get all
    flux get helmreleases -A
    flux get kustomizations --watch