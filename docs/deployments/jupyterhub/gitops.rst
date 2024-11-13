.. _jupyterlab-gitops: 

JupyterHub deployment with GitOps
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
