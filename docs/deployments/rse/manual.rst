.. _storm-webdav:


RUCIO RSE - WebDAV
==================



Prerequisites
-------------

Configure your IAM A&A account and create a IAM client following the next steps: https://ska-telescope.gitlab.io/src/kb/ska-src-docs-operator/services/local/mandatory/rucio-storage-element/rucio-storage-element.html#iam-configuration


Then it is necessary to prepare a storage where Rucio will place the files and replicas assigned to espSRC. 
For this, it is necessary to connect a storage unit to the node where the WebDav service is installed.  

To create a CephFS with 20TB:

.. code-block:: bash

    ``openstack share create --share-type cephfstype --name rucio-shared cephfs 20480``


Then, the configuration and mounting of this directory is automatic at node instantiation time. 
However, to do it manually, we apply the following command on each node:

.. code-block:: bash
    
    sudo mkdir /storage/dteam/disk/
    sudo chown storm:storm /storage/dteam/disk/
    sudo mount -t ceph 172.16.5.115:6789,172.16.5.116:6789,172.16.5.117:6789:/volumes/_nogroup/12581a31-7af3-4451-8fe8-e54f5409d293 \
                  /storage/dteam/disk/ \
                  -o name=rucio-rse-stormwebdav \
                  -o secretfile=/etc/ceph/ceph.client.rucio-shared.secret



Service Configuration and Deployment Steps
------------------------------------------

.. note:: 

    Installation on Rocky Linux 9


Install packages and add user for `storm-webdav`:

.. code-block:: bash

    sudo yum -y install epel-release redhat-lsb-core wget git tar && \\ 
    sudo yum update -y && \\ 
    sudo yum install -y yum-utils gfal2-all davix attr acl sudo && \\ 
    sudo echo '%wheel ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers && \\
    sudo rpm --import http://repository.egi.eu/sw/production/umd/UMD-RPM-PGP-KEY && \\ 
    sudo yum install -y http://repository.egi.eu/sw/production/umd/4/centos7/x86_64/updates/umd-release-4.1.3-1.el7.centos.noarch.rpm && \\
    sudo adduser --uid ${STORM_USER_UID} storm && \\ 
    sudo usermod -a -G wheel storm && \\
    sudo yum-config-manager --add-repo https://repo.cloud.cnaf.infn.it/repository/storm/nightly/storm-nightly-centos7.repo && \\ 
    sudo yum install -y storm-webdav voms-clients-java jq &&  \\
    sudo yum clean all

Then, get the `storm-webdav` package that is compatible with CentOS flavours:

.. code-block:: bash

    curl https://repo.cloud.cnaf.infn.it/repository/storm-rpm-stable/centos7/storm-webdav-1.4.2-1.el7.noarch.rpm --output storm-webdav-1.4.2-1.el7.noarch.rpm

Install this package manually:

.. code-block:: bash

    sudo yum localinstall -y storm-webdav-1.4.2-1.el7.noarch.rpm

Once installed, proceed with the SSL certificates installation. To do it, include your certificates within ```/etc/grid-security/storm-webdav/``` with the following names:

- ```hostcert.pem``` - `SSL Certificates chain`
- ```hostkey.pem``` - `SSL Private Key`


Create a ```storm-webdav``` properties files within ```/etc/storm/webdav/sa.d/storm-webdav-sa.properties```:

.. code-block:: bash
    
    sudo vi /etc/storm/webdav/sa.d/storm-webdav-sa.properties


.. note::
   At this point, you should have your storage backend set up, connected and ready for use, having a folder that will be used to store the Rucio RSE data. In this installation we are using ```/storage/dteam/disk``` as data folder.


Modify the next configuration variables in this file ```/etc/storm/webdav/sa.d/storm-webdav-sa.properties```:

.. code-block:: bash
    
    name=<Name of the Storage webdav>
    rootPath=<Path to the folder where Rucio will store its data>
    accessPoints=<Initial access point folder>
    orgs=<URL of the IAM provider or providers>

    anonymousReadEnabled=false
    voMapEnabled=false

    orgsGrantReadPermission=true
    orgsGrantWritePermission=true
    wlcgScopeAuthzEnabled=true

The next example use ```/storage/dteam/disk``` as datafolder and ```/disk``` as startup folder for the data. Then the IAM A&A service used here is ```https://iam-escape.cloud.cnaf.infn.it/```.

.. code-block:: bash
    
    name=dteam-disk
    rootPath=/storage/dteam/disk
    accessPoints=/disk
    orgs=https://iam-escape.cloud.cnaf.infn.it/,https://ska-iam.stfc.ac.uk/

    anonymousReadEnabled=false
    voMapEnabled=false

    orgsGrantReadPermission=true
    orgsGrantWritePermission=true
    wlcgScopeAuthzEnabled=true

Then, lets configure the IAM A&A client for ```storm-webdav```. To do it, edit the next file:

.. code-block:: bash
    
    sudo vi /etc/storm/webdav/config/application.ym

Include the next, changing ```client-name```, ```client-id``` and ```client-secret``` with the client your previously created in the preliminary step. Maintaing the ```issuer``` and ```issuer-uri``` as follows:

.. code-block:: bash

    oauth:
    enable-oidc: true
    issuers:
        - name: escape
        issuer: https://iam-escape.cloud.cnaf.infn.it/
    spring:
    security:
        oauth2:
        client:
            provider:
            escape:
                issuer-uri: https://iam-escape.cloud.cnaf.infn.it/
            registration:
            escape:
                provider: escape
                client-name: <YOUR_CLIENT_NAME>
                client-id: <YOUR_CLIENT_ID>
                client-secret: <YOUR_CLIENT_SECRET>
                scope:
                - openid
                - profile
                - wlcg.groups
    storm:
    voms:
        trust-store:
        dir: ${STORM_WEBDAV_VOMS_TRUST_STORE_DIR:/etc/grid-security/certificates}

The next step is to configure the ```storm-webdav``` web service. Edit the next file:

.. code-block:: bash
    
    sudo vi /etc/systemd/system/storm-webdav.service.d/storm-webdav.conf

And complete it the values to fit it to your computing environment and web preferences, taking into account the following *critical* parameters:

- ```STORM_WEBDAV_HOSTNAME_0``` must match with the hostname of your node.
- ```STORM_WEBDAV_HTTPS_PORT``` and ```STORM_WEBDAV_HTTP_PORT``` according to your preferences.
- ```STORM_WEBDAV_CERTIFICATE_PATH``` and ```STORM_WEBDAV_PRIVATE_KEY_PATH``` pointing to the folder with the SSL private key and SSL Certs chain. 

.. code-block:: bash

    [Service]
    Environment="STORM_WEBDAV_USER=storm"
    Environment="STORM_WEBDAV_JVM_OPTS=-Xms1024m -Xmx1024m"
    Environment="STORM_WEBDAV_SERVER_ADDRESS=0.0.0.0"
    Environment="STORM_WEBDAV_HOSTNAME_0=test-rockylinux.novalocal"
    Environment="STORM_WEBDAV_HTTPS_PORT=8443"
    Environment="STORM_WEBDAV_HTTP_PORT=8085"
    Environment="STORM_WEBDAV_CERTIFICATE_PATH=/etc/grid-security/storm-webdav/hostcert.pem"
    Environment="STORM_WEBDAV_PRIVATE_KEY_PATH=/etc/grid-security/storm-webdav/hostkey.pem"
    Environment="STORM_WEBDAV_TRUST_ANCHORS_DIR=/etc/grid-security/certificates"
    Environment="STORM_WEBDAV_TRUST_ANCHORS_REFRESH_INTERVAL=86400"
    Environment="STORM_WEBDAV_MAX_CONNECTIONS=300"
    Environment="STORM_WEBDAV_MAX_QUEUE_SIZE=900"
    Environment="STORM_WEBDAV_CONNECTOR_MAX_IDLE_TIME=30000"
    Environment="STORM_WEBDAV_SA_CONFIG_DIR=/etc/storm/webdav/sa.d"
    Environment="STORM_WEBDAV_JAR=/usr/share/java/storm-webdav/storm-webdav-server.jar"
    Environment="STORM_WEBDAV_LOG=/var/log/storm/webdav/storm-webdav-server.log"
    Environment="STORM_WEBDAV_OUT=/var/log/storm/webdav/storm-webdav-server.out"
    Environment="STORM_WEBDAV_ERR=/var/log/storm/webdav/storm-webdav-server.err"
    Environment="STORM_WEBDAV_LOG_CONFIGURATION=/etc/storm/webdav/logback.xml"
    Environment="STORM_WEBDAV_ACCESS_LOG_CONFIGURATION=/etc/storm/webdav/logback-access.xml"
    Environment="STORM_WEBDAV_VO_MAP_FILES_ENABLE=false"
    Environment="STORM_WEBDAV_VO_MAP_FILES_CONFIG_DIR=/etc/storm/webdav/vo-mapfiles.d"
    Environment="STORM_WEBDAV_VO_MAP_FILES_REFRESH_INTERVAL=21600"
    Environment="STORM_WEBDAV_TPC_MAX_CONNECTIONS=50"
    Environment="STORM_WEBDAV_TPC_MAX_CONNECTIONS_PER_ROUTE=25"
    Environment="STORM_WEBDAV_TPC_VERIFY_CHECKSUM=false"
    Environment="STORM_WEBDAV_TPC_TIMEOUT_IN_SECS=30"
    Environment="STORM_WEBDAV_TPC_TLS_PROTOCOL=TLSv1.2"
    Environment="STORM_WEBDAV_TPC_REPORT_DELAY_SECS=5"
    Environment="STORM_WEBDAV_TPC_ENABLE_TLS_CLIENT_AUTH=false"
    Environment="STORM_WEBDAV_TPC_PROGRESS_REPORT_THREAD_POOL_SIZE=4"
    Environment="STORM_WEBDAV_AUTHZ_SERVER_ENABLE=false"
    Environment="STORM_WEBDAV_REQUIRE_CLIENT_CERT=false"
    Environment="STORM_WEBDAV_USE_CONSCRYPT=false"
    Environment="STORM_WEBDAV_TPC_USE_CONSCRYPT=false"
    Environment="STORM_WEBDAV_ENABLE_HTTP2=false"


Finally, restart the ```storm-webdav``` to apply the changes:

.. code-block:: bash

    sudo systemctl stop storm-webdav
    sudo systemctl start storm-webdav
    sudo systemctl status storm-webdav

Post-Deployment Verification
----------------------------

Once the service is initialised, we can check the logs to see if everything is correct:

.. code-block:: bash
    
    sudo tail -f -n 100  /var/log/storm/webdav/storm-webdav-server.log
    sudo tail -f -n 100  /var/log/storm/webdav/storm-webdav-server-access.log
    sudo tail -f -n 100  /var/log/storm/webdav/storm-webdav-server.er

Proxy configuration
^^^^^^^^^^^^^^^^^^^

Because espSRC maintains a proxy in several of the services, this WebDav service is 
redirected from a proxy that provides the traffic routing, for this the corresponding rule 
for port ``18027`` (proxy) to ``8443`` (webdav host) is added to the Firewall.

Access to the service
^^^^^^^^^^^^^^^^^^^^^

Then access to the endpoint: https://spsrc14.iaa.csic.es:18027/disk

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
  export ENDPOINT_URL=https://spsrc14.iaa.csic.es:18027/disk 
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

Renewal of SSL certificates
^^^^^^^^^^^^^^^^^^^^^^^^^^^

This causes the service to not connect correctly with the SKAO Rucio Server Global, so the 
information panels and monitoring metrics will have a marked problem. 
This requires the use of a tool to be able to prepare the certificate a few days before the expiry date. 

1. Check if the systemd timer is enabled: ``systemctl list-timers | grep certbot``
2. Enable the Certbot systemd timer (if not already enabled): ``sudo systemctl enable certbot.timer`` and  ``sudo systemctl start certbot.timer``
3. Check the status of the timer: ``sudo systemctl status certbot.timer`` The timer is configured to run twice 
a day and renew any certificates that are within 30 days of expiration.
