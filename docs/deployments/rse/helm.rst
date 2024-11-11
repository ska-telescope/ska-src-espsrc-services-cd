.. _storm-webdav-helm:

Rucio RSE - Helm
================

.. tip::
    
    espSRC Rucio-RSE endpoint: https://rucio.espsrc.iaa.csic.es/disk  (in progress)

Prerequisites
-------------

Configure your IAM A&A account and create a IAM client following the next steps: https://ska-telescope.gitlab.io/src/kb/ska-src-docs-operator/services/local/mandatory/rucio-storage-element/rucio-storage-element.html#iam-configuration

Then it is necessary to prepare a storage where Rucio will place the files and replicas assigned to espSRC. 
For this, it is necessary to connect a storage unit to the node where the WebDav service is installed.  

To create a CephFS with 10TB:

.. code-block:: bash

    openstack share create --share-type cephfstype --name rucio-shared cephfs 10240


Then, the configuration and mounting of this directory is automatic at node instantiation time. 
However, to do it manually, we apply the following command on each node:

.. code-block:: bash
    
    sudo mkdir /storage/dteam/disk/
    sudo chown storm:storm /storage/dteam/disk/
    sudo mount -t ceph 172.16.5.115:6789,172.16.5.116:6789,172.16.5.117:6789:/volumes/_nogroup/12581a31-7af3-4451-8fe8-e54f5409d293 \
                  /storage/dteam/disk/ \
                  -o name=rucio-rse-stormwebdav \
                  -o secretfile=/etc/ceph/ceph.client.rucio-shared.secret

A kubernetes cluster with a version greater than v1.22 with helm installed:

.. code-block:: bash

    curl -fsSL -o get_helm.sh https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3
    chmod 700 get_helm.sh
    ./get_helm.sh


Service Configuration and Deployment Steps
------------------------------------------


