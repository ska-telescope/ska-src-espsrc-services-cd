.. jupyterlab-helm

JupyterHub deployment with Helm Chart
=====================================

JupyterHub is a powerful multi-user platform that provides Jupyter notebook environments 
to various users, ideal for education, research, and collaborative projects. 
Deploying JupyterHub on a Kubernetes cluster enables seamless scalability and centralized 
resource management, allowing multiple users to access individual, isolated notebook 
instances through a single, unified interface.

**Helm** simplifies the deployment of JupyterHub on Kubernetes by packaging configuration
files and resources into reusable "charts." Using the Helm chart for JupyterHub streamlines setup, 
allowing you to quickly deploy and manage configurations, including integration with Kubernetes 
secrets, storage, and authentication systems.


Prerequisites
-------------

Kubernetes Cluster
^^^^^^^^^^^^^^^^^^

Ensure you have a running Kubernetes cluster with at least the next versions:

```{note}
Client Version: v1.30.6+k3s1
Kustomize Version: v5.0.4-0.20230601165947-6ce0bf390ce3
Server Version: v1.30.6+k3s1
```

Helm
^^^^ 

Install Helm for deploying this JupyterHub Chart

.. code-block:: bash

   curl -fsSL -o get_helm.sh https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3
   chmod 700 get_helm.sh
   ./get_helm.sh


Vault and External Secrets
^^^^^^^^^^^^^^^^^^^^^^^^^^

Ensure Vault is configured, with necessary secrets accessible in External Secrets (see GitOps for JupyterHub)

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

```{note}

Previously to do this step you must have created the CephFS storage with the following procedure for a 20TB storage folder:

``openstack share create --share-type cephfstype --name k8s-shared cephfs 20480``

```

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


Service Configuration
---------------------

To configure the service we need a ``values.yaml`` file to set the variables and directives that JupyterHub needs:

.. code-block:: yaml

    proxy:
    secretToken: "<SECRET TOKEN>"
    service:
        type: NodePort
        nodePorts:
        http: <NODE PORT>

    hub:
    config:
        Authenticator:
        enable_auth_state: true
        allow_all: true
        GenericOAuthenticator:
        login_service: "SKA IAM Prototype"
        client_id: <CLIENT ID>
        client_secret: <CLIENT SECRET>
        oauth_callback_url: https://notebook.espsrc.iaa.csic.es/hub/oauth_callback
        authorize_url: https://ska-iam.stfc.ac.uk/authorize
        token_url: https://ska-iam.stfc.ac.uk/token
        userdata_url: https://ska-iam.stfc.ac.uk/userinfo
        scope:
            - openid
            - profile
            - email
            - offline_access
        userdata_token_method: GET
        userdata_params: {'state': 'state'}
        username_key: preferred_username
        JupyterHub:
        authenticator_class: generic-oauth

    extraConfig:
        logoConfig: |
            import urllib.request
            urllib.request.urlretrieve("https://raw.githubusercontent.com/manuparra/espsrc-science-platform/main/espsrc.png", "espsrc.png")
            c.JupyterHub.logo_file = '/srv/jupyterhub/espsrc.png'

    baseUrl: /

    db:
        pvc:
        storageClassName: local-path

    singleuser:
    memory:
        limit: 1G
        guarantee: 1G

    cpu:
        limit: .5
        guarantee: .5

    storage:
        dynamic:
        storageClass: local-path
        capacity: 1Gi

    # Defines the default image
    defaultUrl: "/lab"
    extraEnv:
        JUPYTERHUB_SINGLEUSER_APP: "jupyter_server.serverapp.ServerApp"
    image:
        name: jupyter/minimal-notebook
        tag: latest
    profileList:
        - display_name: "Minimal environment"
        description: "A Python environment."
        default: true
        - display_name: "Datascience environment"
        description: "Python, R and Julia environments."
        kubespawner_override:
            image: jupyter/datascience-notebook:latest

Change the next: 

-  ``"<SECRET TOKEN>"`` is a 32 bytes HEX string
-  ``"<NODE PORT>"`` is the port to connect the service locally within the cluster. 
-  ``"<CLIENT ID>"`` is the ID of the SKAO-IAM client created.
-  ``"<CLIENT SECRET>"`` id the secret/password of the SKAO-IAM client created.


Deployment Steps
----------------



Post-Deployment Verification
----------------------------

Troubleshooting
---------------