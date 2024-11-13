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

Clone this repository:

.. code-block:: bash

    git clone https://gitlab.com/ska-telescope/src/deployments/espsrc/ska-src-espsrc-services-cd.git

Create a ``values.yaml`` file with the next:

.. code-block:: bash

    image:
        repository: registry.gitlab.com/ska-telescope/src/ska-rucio-prototype/ska-src-storm-webdav
        tag: 1.1.1
        pullPolicy: Always

    deployment:
        namespace: rucio-espsrc-rse

    extraEnv:
    - name: STORM_WEBDAV_HOSTNAME_0
        value:
    - name: STORM_WEBDAV_VOMS_TRUST_STORE_DIR
        value: /etc/grid-security/certificates
    - name: STORM_WEBDAV_REQUIRE_CLIENT_CERT
        value: "false"

    config:
    # refer to https://github.com/italiangrid/storm-webdav/tree/master/etc/storm-webdav/config
    application: |- 
        oauth: 
        enable-oidc: true
        issuers:
            - name: escape
            issuer: https://iam-escape.cloud.cnaf.infn.it/
            - name: ska
            issuer: https://ska-iam.stfc.ac.uk/
        spring:
        security:
            oauth2:
            client:
                provider:
                escape:
                    issuer-uri: https://iam-escape.cloud.cnaf.infn.it/
                ska:
                    issuer-uri: https://ska-iam.stfc.ac.uk/
                registration:
                escape:
                    provider: escape
                    client-name: 
                    client-id: 
                    client-secret: 
                    scope:
                    - openid
                    - profile
                    - wlcg.groups
 
    # list of storage areas
    sa:
        # refer to https://github.com/italiangrid/storm-webdav/tree/master/etc/storm-webdav/sa.d
        sa.properties: |-
        # Name of the storage area
        name=sa

        # Root path for the storage area. Files will be served from this path, which must exist and
        # must be accessible from the user that runs the storm webdav service
        rootPath=

        # Comma separated list of storage area access points.
        accessPoints=

        # Comma-separated list of VOMS VOs supported in this storage area
        # vos=test.vo

        # Comma-separated list of OAuth/OpenID Connect token issuers trusted in this storage area
        orgs=https://iam-escape.cloud.cnaf.infn.it/,https://ska-iam.stfc.ac.uk/

        # Enables read access to users authenticated with an X.509 certificate issued by
        # a trusted CA (users without VOMS credentials).
        # Defaults to false, which means that all users need to authenticate with a VOMS credential
        # authenticatedReadEnabled=false

        # Enables read access to anonymous users. Defaults to false.
        anonymousReadEnabled=false

        # Enables VO map files for this storage area. Defaults to true.
        voMapEnabled=false

        # VO map normally grants read-only access to storage area files. To grant
        # write access set this flag to true. Defaults to false.
        # voMapGrantsWriteAccess=false

        # Enables read access to storage area files to users authenticated using OAuth/OIDC. Defaults to true.
        orgsGrantReadPermission=true

        # Enables write access to storage area files to users authenticated using OAuth/OIDC. Defaults to false.
        orgsGrantWritePermission=true

        # Enables scope-based authorization following the rules imposed by the WLCG JWT profile. Defaults to false.
        #wlcgScopeAuthzEnabled=true

        # Enables fine-grained authorization engine. Defaults to false.
        #fineGrainedAuthzEnabled=true

    persistence:
        storageClass: 
        existingClaim: ""
        enabled: true
        accessMode: ReadWriteOnce
        size: 2500Gi

Update the next items within this ``values.yaml``:

- ``client-name``: client name for the SKAO-IAM client created
- ``client-id``: id of the SKAO-IAM client
- ``client-secret``: secret for the SKAO-IAM client
- ``extraEnv.STORM_WEBDAV_HOSTNAME_0``: the hostname serving this StoRM instance rucio.espsrc.iaa.csic.es
- ``extraEnv.STORM_WEBDAV_REQUIRE_CLIENT_CERT``: "false", due to we are serving HTTP sitting behind a TLS termination proxy
- ``config.certificates.host.crt``: -
- ``config.certificates.host.key``: - 
- ``config.sa.sa.properties``: the storage area properties file with values ``rootPath``=``/storage/dteam/disk`` and ``accessPoints``=``/disk``
- ``persistence``: attributes to enable persistence of the storage area ``storageClass``=``rucio-rse-sc``


Deployment
^^^^^^^^^^

Once ``values.yaml`` is ready, run the next:

.. code-block:: bash

    helm upgrade --install --create-namespace -n rucio-espsrc-rse --values values.yml ska-src-storm-webdav etc/helm/

Finally, add this new service to the HAProxy configuration.

Post-Deployment Verification
----------------------------

Once the service is initialised in kubernetes, we can check the logs to see if everything is correct:

.. code-block:: bash
    
   kubectl logs <pod_name> -n rucio-espsrc-rse 


Access to the service
^^^^^^^^^^^^^^^^^^^^^

Then access to the endpoint: https://rucio.espsrc.iaa.csic.es/disk

- Check that you can access the service externally.
- Check that the access is SSL based.

To validate that the service is working properly you can apply the connectivity tests.

Connectivity test
^^^^^^^^^^^^^^^^^

Run a connectivity test for the RSE using the `operator toolbox <https://gitlab.com/ska-telescope/src/operations/ska-src-operator-toolbox>`. 
To perform this action you can follow the instructions:

. note::

   Verify that you have docker installed on the machine from which you are going to launch the SKAO Datalake connectivity tests.


Clone this repository:

.. code-block:: bash

  git clone https://gitlab.com/ska-telescope/src/operations/ska-src-operator-toolbox.git
  cd ska-src-operator-toolbox


Then export the next data:

.. code-block:: bash

  export RUCIO_CFG_ACCOUNT=<your SKAO IAM username>
  export ENDPOINT_URL=<your RSE URL including the path>
  export RSE=<name of RSE to test the conectivity> 
  export DEBUG="False"



For example, if you want to test the ESPSRC RSE: 

.. code-block:: bash

  export RUCIO_CFG_ACCOUNT=mparra
  export ENDPOINT_URL=https://rucio.espsrc.iaa.csic.es/disk 
  export RSE=ESPSRC_STORM
  export DEBUG="False"


Finally, run the next:

.. code-block:: bash

  $ docker run -it --rm \
        -e RUCIO_CFG_ACCOUNT=$RUCIO_CFG_ACCOUNT \
        -e DEBUG="True" \
        -e CMD="/opt/ska-src-operator-toolbox/bin/report_rse_connectivity.sh --endpoint-url $ENDPOINT_URL --rse $RSE" \
        registry.gitlab.com/ska-telescope/src/operations/ska-src-operator-toolbox:latest

After this, `operator toolbox <https://gitlab.com/ska-telescope/src/operations/ska-src-operator-toolbox>` will 
show a report of the results of the connectivity test.


Functional tests and SKAO Datalake monitoring
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Once the RSE has joined the SKAO Datalake and the connectivity tests 
have been successful, the next step is to verify that the RSE is being 
monitored through the functional tests and the RSE appears in Grafana. 

This procedure is automatic once the RSE is added to SKAO Datalake by 
the Rucio Server operators, so you only need to check that your RSE 
appears in the following monitoring platform 
`SKAO Monitoring <https://monit.srcdev.skao.int/grafana/login>` within 
the dashboard `Rucio events`.

Troubleshooting
---------------
Part of the problems reported with WebDav and Rucio RSE stem from storage space management, 
storage directory permissions or connectivity with the SKAO-IAM client.

Here are some of the most common issues encountered in deployment.

Problem with permissions
^^^^^^^^^^^^^^^^^^^^^^^^
Check that the RSE storage directory has the permissions of the user ``storm`` and the group ``storm``. 
Check that your storage unit and drive mount support extended Attributes for the file system.

Issues with the storageClass
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A critical part is to provide 
a suitable StorageClass for storage for the RSE. In our case this has been provided through a (shared) 
CephFS using a specific local-path for it. The rest of the components go to a different StorageClass.
