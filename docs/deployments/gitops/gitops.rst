.. _gitops: 

GitOps setup at espSRC
======================

In this document, we will describe the installation process of each of the 
components that provide the installation capabilities of the espSRC services for the 
SRCNet v.0.1 based on GitOps. 
These methods install the main components to be able to work with GitOps on the 
repository where all the deployments are stored:

https://gitlab.com/ska-telescope/src/deployments/espsrc/ska-src-espsrc-services-cd

Pre-requisites
--------------
- A kubernetes cluster ready. Version >= 1.22.
- Helm installed and ready.
- StorageClass ready.

Then install the next components: Vault, External Secrets Operator and finally FluxCD.

Install Vault
-------------

Add repos for Vault:

.. code:: bash

    helm repo add hashicorp https://helm.releases.hashicorp.com
    helm repo update

Create a namespace for Vault:

.. code:: bash

    kubectl create namespace vault

Install Vault:

.. code:: bash
    
    helm install vault hashicorp/vault --namespace vault 
    kubectl get pods -n vault

Check the status (vault-0 could be 0/1 until you init and unseal the service):

.. code:: bash

    NAME                                    READY   STATUS    RESTARTS   AGE
    vault-0                                 1/1     Running   0          1m
    vault-agent-injector-6c9b77ff56-vs5hv   1/1     Running   0          1m


Initialize Vault:

.. code:: bash
    
    kubectl exec -it vault-0 -n vault -- vault operator init

.. note:: 

    Get and store all the Keys and Root Secret in a safe place.

Useal the Vault storage: 

.. code:: bash
    
    kubectl exec -it vault-0 -n vault -- vault operator unseal


Access the pod and login as root with the values generates in the previous step:

.. code:: bash
    
    kubectl exec -ti vault-0 -- /bin/sh
    vault login

Then create a ``path`` in Vault for ``kv-v2`` i.e. ``app``.

.. code:: bash
    
    vault secrets enable -path=app kv-v2

Enable kubernetes authentication:

.. code:: bash

    vault auth enable kubernetes

Then apply configuration:

.. code:: bash
    
    vault write auth/kubernetes/config kubernetes_host="https://kubernetes.default.svc"

Now we can create Vault secrets, for example following this template (this is for this example, to see the specific values and secrets go to the ``/app/<service>/gitops/``):

.. code:: bash
    # Create a secret in Vault
    vault kv put app/test clientsecret="...Secret goes here..."

Create a Policy for the secret created previously (this is for this example, to see the specific values and secrets go to the ``/app/<service>/gitops/``):

.. code:: bash

    vault policy write test-policy - <<EOF
    > path "app/data/test" {
    >    capabilities = ["read"]
    > }
    > EOF
    Success! Uploaded policy: test-policy

Create a Vault role that binds a Kubernetes service account to a policy (and the policy will refer to the secret) (this is for this example, to see the specific values and secrets go to the ``/app/<service>/gitops/``):

.. code:: bash

    vault write auth/kubernetes/role/test \
    >       bound_service_account_names=test \
    >       bound_service_account_namespaces=test \
    >       policies=test-policy \
    >       ttl=24h
    Success! Data written to: auth/kubernetes/role/test


Install External Secrets Operator
---------------------------------

Install the Helm repo and install the Helm itself:

.. code:: bash

    helm repo add external-secrets https://charts.external-secrets.io
    helm install external-secrets external-secrets/external-secrets -n external-secrets --create-namespace

Check the pods:

.. code:: bash

    kubectl get pods -n external-secrets
    NAME                                                READY   STATUS    RESTARTS      AGE
    external-secrets-7f9f5fd4d6-6zld6                   1/1     Running   2 (27h ago)   19d
    external-secrets-cert-controller-7b795c658b-26hmt   1/1     Running   1 (27h ago)   19d
    external-secrets-webhook-576774cb7c-g2dwq           1/1     Running   1 (27h ago)   19d

.. note::

    Each application to be deployed within the cluster by using GitOps will include these 4 components: ``ClusterRole``, ``ClusterRoleBinding``, ``SecretStore`` and ``ExternalSecret`` and all the extra configurations for ``kustomize``.



ClusterRole and ClusterRoleBinding
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. note::
    This is an example. To see the specific ClusterRoleBinding go to folder ``/apps/<service>/gitops/``. 

This is mandatory to enable RBAC authorization. This will create a ClusterRoleBinding that associates with a ServiceAccount.

.. code:: bash

    apiVersion: rbac.authorization.k8s.io/v1
    kind: ClusterRoleBinding
    metadata:
        name: vault-access-rolebinding
    roleRef:
        kind: ClusterRole
        name: system:auth-delegator
        apiGroup: rbac.authorization.k8s.io
    subjects:
    - kind: ServiceAccount
        name: test
        namespace: test

SecretStore
^^^^^^^^^^^

.. note::
    This is an example. To see the specific SecretStore and Secrets deployed for each app go to folder ``/apps/<service>/gitops/``. 


Create a SecretStore resource that gives your existing service account (e.g. test) access to vault. 
You may need to change the commented values in the below example depending on how your vault instance 
is set up.

.. code:: bash

    apiVersion: external-secrets.io/v1beta1
    kind: SecretStore
    metadata:
    name: vault-backend
    namespace: test
    spec:
    provider:
        vault:
            # Address of your vault instance within the Kubernetes cluster
            server: "http://vault.vault.svc.cluster.local:8200"
            path: "app"
            version: "v2"
            auth:
                kubernetes:
                # Path where the Kubernetes authentication backend is mounted in your vault setup
                mountPath: "kubernetes"
                # A required field containing the vault Role to assume.
                role: "test"
                # Optional service account field containing the name
                # of a kubernetes ServiceAccount
                serviceAccountRef:
                    name: "test"

ExternalSecret
^^^^^^^^^^^^^^

.. note::
    This is an example. To see the specific ExternalSecret and the secrets for the apps go to folder ``/apps/<service>/gitops/``. 

Create an ExternalSecret manifest that refers to the SecretStore above. The target is the name of the secret 
that will be created and the secretKey is the name of the key that will appear inside the created secret. The 
key is the path to the secret in vault and the property is the key within the secret inside vault.

.. code:: bash

    apiVersion: external-secrets.io/v1beta1
    kind: ExternalSecret
    metadata:
    name: test
    namespace: test
    spec:
    refreshInterval: "15s" # time to sync from vault
    secretStoreRef:
        name: vault-backend # name of the SecretStore you created
        kind: SecretStore
    target:
        name: this-secret-is-from-vault # name that the secret will have in the Kubernetes cluster
        creationPolicy: Owner # create secret if not exists
    data:
        - secretKey: clientkey-from-vault # key that the secret will contain in the Kubernetes cluster
        remoteRef:
            key: app/data/test # path to secret in vault
            property: clientsecret # key in the vault secret

Validation
^^^^^^^^^^

Inspect the secret in Kubernetes to ensure that it was created properly. Based on the ExternalSecret configuration 
a secret was created with the name this-secret-is-from-vault and the data contains the key clientkey-from-vault. 
The value of the secret should be the same value as in the secret stored in vault.

.. code:: bash

    kubectl describe secret -n test
    Name:         this-secret-is-from-vault
    Namespace:    test
    Labels:       reconcile.external-secrets.io/created-by=dba9473717534a2fdbc767b24224952b
    Annotations:  reconcile.external-secrets.io/data-hash: 3be9022b909020a93ed761d550affbfb

    Type:  Opaque

    Data
    ====
    clientkey-from-vault:  3 byte



Install FluxCD CLI
------------------

.. code:: bash

    curl -s https://fluxcd.io/install.sh | sudo bash


Install the FluxCD Bootstrap:

.. code:: bash
    
    export GITLAB_TOKEN=<gl-token>

You will need a GitLab Token to allow this interaction with the repository and the cluster, change ``<gl-token>`` with your token.

Then run the flux bootstrap aganist the apps included within the ``/apps`` folder in ``ska-telescope/src/deployments/espsrc/ska-src-espsrc-services-cd`` repository.

.. code:: bash
    
    flux bootstrap gitlab   \ 
        --owner=ska-telescope/src/deployments/espsrc   \ 
        --repository=ska-src-espsrc-services-cd   --branch=main   \ 
        --path=./apps   --personal   --deploy-token-auth

This folder has all the deployments based on gitops ready to deploy. Once you start this bootstrap, you can chek the status of the deployments stored in this folder in our repo. 
Follow the instruction of the deployment to configure the ``kustomization`` itself. See ``/apps/<service>/gitops/`` folders with the ``kustomization`` files and values.

Validation and checks
^^^^^^^^^^^^^^^^^^^^^

Check the overall status of the helm releases and kustomizations:

.. code:: bash

    flux get all
    flux get helmreleases -A
    flux get kustomizations --watch

If you want to stop syncronisation you can suspend the deployments by using the next:

.. code:: bash
    
    flux get kustomizations
    flux get sources git
    flux get helmreleases -A

    flux suspend kustomization flux-system
    flux suspend helmrelease <release> -n <namespace>
    flux suspend source git flux-system
    flux suspend source helm <release-git-repo>
    flux suspend source chart <chart>

