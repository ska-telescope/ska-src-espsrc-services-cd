.. _soda:

SODA Service
============

.. info ::
    
    espSRC Rucio-RSE endpoint: https://soda.espsrc.iaa.csic.es 

The SODA (Service for Data Access) service is a standardized protocol designed to 
facilitate data retrieval and management in the field of astronomy. Based on the 
IVOA (International Virtual Observatory Alliance) [https://ivoa.net/documents/SODA/20170517/index.html] standards, SODA provides a consistent 
interface for accessing subsets of large astronomical datasets, enabling researchers to 
retrieve only the necessary portions of data instead of downloading entire files.

This selective access reduces data transfer times, optimizes storage usage, and supports 
advanced data operations like cutouts, filtering, and transformations directly on the server 
side. By integrating SODA into their workflows, astronomers can efficiently handle large-scale 
observations and streamline their data analysis processes, making it an essential tool for 
research involving vast astronomical surveys and archives.

Features: 
- It understands FITS-structures and can extract and generate cuts from FITS-files of considerable sizes based on astronomical  coordinates. 
- It saves bandwidth by downloading only the needed portions data.
- It recognizes standard FITS WCS axes encoding.
- Current implementation relies on POSIX-like data storage.

Prerequisites
-------------

There is a docker images are stored under SKA-Harbor: `harbor.srcdev.skao.int/soda/visivo-vlkb-soda:1.7`. For deployment using docker, you will need some files local to the docker daemon that the SODA service can read.

Access to local RSE - CephFS
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

SODA needs access to the local file system where the RSE data is stored. To do so, access to the storage unit must be provided on the node where the SODA service is connected. 

In our case the configuration of the storage unit is as follows:

.. code-block:: bash
    
    sudo mount -t ceph 172.16.5.115:6789,172.16.5.116:6789,172.16.5.117:6789:/volumes/_nogroup/12581a31-7af3-4451-8fe8-e54f5409d293 /storage/dteam/disk -o name=rockylinux-rse -o secretfile=/etc/ceph/keyring

where ``/storage/dteam/disk`` is the folder in CephFS. 

Service Configuration
---------------------

Create a ``docker-compose.yaml`` change ``./<your POSIX RSE path>`` with the corresponing 
path in your RSE, in our case it needs to be pointing to ``/storage/dteam/disk/dev/deterministic/``.

.. note:: 

    Change the output port ``18025`` (TLS) and ``18019`` with the current ports availables. In our case, we are using a Proxy to redirect requests from the an external endpoint to the SODA service.

.. code-block:: bash
    
    version: '3'
    
    services:
    
    ska:
        container_name: ska
        image: harbor.srcdev.skao.int/soda/visivo-vlkb-soda:1.7
        user: 5000:5000
        ports:
        - 18019:8080
        environment:
        - ACCESS_CONTEXT_ROOT=ska#datasets
        volumes:
        - /storage/dteam/disk/dev/deterministic/:/srv/datasets:ro
    
    
    ska-tls:
        container_name: ska-tls
        image: harbor.srcdev.skao.int/soda/visivo-vlkb-soda:1.7
        user: 5000:5000
        ports:
        - 18025:8443
        environment:
        - ACCESS_CONTEXT_ROOT=ska#datasets
        - KEYSTORE_ALIAS=tomcat
        volumes:
        - /storage/dteam/disk/dev/deterministic/:/srv/datasets:ro
        - ./security/keystore.jks:/etc/pki/tls/keystore.jks:ro
        - ./security/keystore.pwd:/etc/pki/tls/keystore.pwd:ro
    
Deployment Steps
----------------

To deploy the SODA service run:

.. code-block:: bash

    docker compose up -d

To un-deploy:

.. code-block:: bash

    docker compose down -d


Post-Deployment Verification
----------------------------

By default, the SODA server will be available at the port mapped to the container's internal port. Following the examples in 
previous steps, the data can be accessed and downloaded into ``soda.fits`` file as: 

Using SKAO-IAM token: 

.. code-block:: bash

    curl --get \
    --oauth2-bearer $TOKEN \
    --data-urlencode "ID=ivo://auth.example.org/datasets/fits?MKT-MGCLS/Abell_194_IPoln.fits" \
    --data-urlencode "CIRCLE=21.4458 -1.373 0.1" \
    -o soda-security-2.fits \
       https://localhost:18025/ska/datasets/soda


For successful request, the requested area (given by CIRCLE, BAND, ...) must at least partially overlap with the FITS-file content.

To make a request with sky coordinates in GALACTIC system using access to the RSE directly (no SKAO-IAM token required):

.. code-block:: bash

    curl -s -k --get --data-urlencode "ID=ivo://auth.example.org/datasets/fits?sp3531_soda/9e/7a/2023-11-09-22-06-30_LoTSS-DR2_P38Hetdex07_mosaic-blanked.fits" \
    --data-urlencode "POS=CIRCLE 110.24 67.14 0.25" \
    --data-urlencode "POSSYS=GALACTIC" \
    -v -o soda-coord-conversion-2-GALACTIC.fits http://spsrc08.iaa.csic.es:18019/ska/datasets/soda

Troubleshooting
---------------

The main problems can come from access to the storage of the RSE Posix. To verify access 
to the data requested from the SODA API, it is necessary that the mapping of the ``/storage/dteam/disk/dev/deterministic/`` 
directory is correctly set in the deployment file in: 

.. code-block:: bash
    ... 
    volumes:
        - /storage/dteam/disk/dev/deterministic/:/srv/datasets:ro

    ... 