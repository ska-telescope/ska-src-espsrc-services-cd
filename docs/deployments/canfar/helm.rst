.. _canfar-helm: 

CANFAR - Helm
=============

.. tip::
    
    espSRC Rucio-RSE endpoint: https://canfar.espsrc.iaa.csic.es 

The CANFAR Science Platform is a cloud-based infrastructure designed to support astronomical research by providing 
scalable data storage, processing, and analysis capabilities. Built on top of the Canadian Advanced Network for Astronomical 
Research (CANFAR), the platform enables researchers to access and analyze large volumes of astronomical data efficiently. 
It integrates services like Jupyter Notebooks, data management tools, and high-performance computing resources, allowing 
scientists to run complex data processing workflows, share results, and collaborate seamlessly. The CANFAR Science Platform 
thus empowers astronomers with a versatile environment for data-intensive research, fostering innovation in the field of astrophysics

Prerequisites
-------------

Services and storage
^^^^^^^^^^^^^^^^^^^^

- A kubernetes cluster (version `1.22` or higher).
- Storage available in the Kubernetes cluster and a Storage Class according to your configuration, for example Cinder, CephFS, or local-path among others, to be used by Persistent Volumes (PV) and Persistent Volumes Claim (PCV).
- A load balancer is available for better performance and functionality.

SKAO-IAM Client 
^^^^^^^^^^^^^^^

Register your client following then next steps: https://ska-telescope.gitlab.io/src/kb/ska-src-docs-operator/services/dependent/iam-client/iam-client.html 

For this service, the scopes required are:

- ``email``
- ``offline_access``
- ``openid``
- ``profile``

    
Get the ``clientID`` and ``clientSecret`` because they will be necessary for serveral components.


StorageClass
^^^^^^^^^^^^ 

Canfar requires to have a StorageClass where the user accounts are stored.
In our deployment we have chosen to provide the cluster with shared storage based on CephFS, so 
each node has mounted by default the ``/mnt/k8s-shared/`` directory. 

.. code-block:: bash
    
    kubectl get sc



The configuration and mounting of this directory is automatic at node instantiation time. 
However, to do it manually, we apply the following command on each node:
`
.. code-block:: bash
    
    sudo mount -t ceph 172.16.5.115:6789,172.16.5.116:6789,172.16.5.117:6789:/volumes/_nogroup/0f611fdf-4c5a-400b-b45a-95be2481333b/6e3395d7-7a17-4e69-899b-370ef1ba42fe \
                  /mnt/k8s-shared/ \
                  -o name=spsrc-k8-cluster00 \
                  -o secretfile=/etc/ceph/ceph.client.k8s-shared.secret

.. important ::

Previously to do this step you must have created the CephFS storage with the following procedure for a 20TB storage folder:

``openstack share create --share-type cephfstype --name k8s-shared cephfs 20480``



Service Configuration
---------------------

PVC and PV creation
^^^^^^^^^^^^^^^^^^^

Add a Persistent Volume (`pv.yaml``) linked to this previously created `StorageClass` with the name `local-path``:

.. code-block:: bash

    apiVersion: v1
    kind: PersistentVolumeClaim
    metadata:
      annotations:
        helm.sh/resource-policy: keep
      name: skaha-pvc
      namespace: skaha-system
    spec:
      accessModes:
        - ReadWriteMany
      volumeMode: Filesystem
      storageClassName: local-path 
      resources:
        requests:
          storage: 10Gi


Add a Persistent Volumen Claim (`pvc.yaml`):


.. code-block:: bash

    apiVersion: v1
    kind: PersistentVolumeClaim
    metadata:
      annotations:
        helm.sh/resource-policy: keep
      name: skaha-workload-cavern-pvc
      namespace: skaha-workload
    spec:
      accessModes:
        - ReadWriteMany
      volumeMode: Filesystem
      storageClassName: local-path  
      resources:
        requests:
          storage: 10G

Finally, create the PV and PVC:

.. code-block:: bash

        kubectl apply -f pv.yaml
        kubectl apply -f pvc.yaml

.. note:: 

    Remember to include the ``Node Affinity`` directive so that the storage is distributed among the nodes.

.. code-block:: bash

    apiVersion: v1
    kind: PersistentVolume
    metadata:
    name: science-platform-volume  # Name is irrelevant
    labels:
        storage: local-path # Labels are VERY relevant.  They should match the values.yaml configuration.
    spec:
    capacity:
        storage: 10Gi
    volumeMode: Filesystem
    accessModes:
        - ReadWriteMany
    persistentVolumeReclaimPolicy: Delete
    storageClassName: local-path
    local:
        path: /mnt/k8s-shared
    nodeAffinity:
        required:
        nodeSelectorTerms:
        - matchExpressions:
            - key: kubernetes.io/hostname
            operator: In
            values:
            - spsrc-k8-cluster00
            - spsrc-k8-cluster01
            - spsrc-k8-cluster02
            - ...

Deployment Steps
----------------

First, add and update CANFAR helm repositories:

.. code-block:: bash

    helm repo add science-platform https://images.opencadc.org/chartrepo/platform
    helm repo add science-platform-client https://images.opencadc.org/chartrepo/client
    helm repo update


Base package
^^^^^^^^^^^^

Install the base helm package for CANFAR. Create a `base.yaml` file with the next content:

.. code-block:: bash

    ---
    skaha:
        namespace: skaha-system
    skahaWorkload:
        namespace: skaha-workload
    secrets:

    #Install traefik as the LoadBalancer and assign the certificate (for self-signed)
    traefik:
        install: true


Then install the base helm package with the values provided in `base.yaml`:

.. code-block:: bash

    helm install --values base.yaml base science-platform/base


posix-mapper deployment
^^^^^^^^^^^^^^^^^^^^^^^

Create a `posix-mapper.yaml` file with the next configuration:

.. warning::
   Change `<HOSTNAME>` according to your setup.

.. code-block:: bash

    # Tell Kubernetes to spin up multiple instances.  Defaults to 1.
    replicaCount: 1

    # It's best to keep these set as such, unless you're willing to change these in several places.
    skaha:
    namespace: skaha-system

    # POSIX Mapper web service deployment
    deployment:
    hostname: <HOSTNAME>    # Change this!
    posixMapper:
        image: images.opencadc.org/platform/posix-mapper:0.2.1
        imagePullPolicy: IfNotPresent
        resourceID: ivo://opencadc.org/posix-mapper
        # Resources provided to the Skaha service.
        resources:
        requests:
            memory: "500M"
            cpu: "500m"
        limits:
            memory: "500M"
            cpu: "500m"

        minUID: 1000
        minGID: 900000
        registryURL: https://spsrc27.iaa.csic.es/reg

    storage:
    service:
        spec:
        persistentVolumeClaim:
            claimName: skaha-pvc # Match this label up with whatever was installed in the base install, or the desired PVC, or create dynamically provisioned storage.

    secrets:
    # These values are preset in the catalina.properties, and this default database only exists beside this service.
    # It's usually safe to leave these as-is, but make sure they match the values in catalina.properties.
    postgresql:
    auth:
        username: posixmapper
        password: posixmapperpwd
        database: mapping
        schema: mapping
    storage:
        spec:
        hostPath:
        path: "/posix-mapper/data"

    # An omission equals true, so set this explicitly.
    base:
    install: false

Then install the `posix-mapper` helm package:

.. code-block:: bash

        helm upgrade --install -n skaha-system  --values posix-mapper.yaml posixmapper science-platform/posixmapper

skaha deployment
^^^^^^^^^^^^^^^^

Create a `skaha.yaml` file with the next configuration:

.. warning::
   Change `<HOSTNAME>` according to your setup.

.. code-block:: bash

    # Skaha web service deployment
    deployment:
    hostname: <HOSTNAME> # Change this!
    skaha:
        # Space delimited list of allowed Image Registry hosts.  These hosts should match the hosts in the User Session images.
        registryHosts: "spsrc26.iaa.csic.es"
        # The group name to verify users against for permission to use the Science Platform.
        usersGroup: "ivo://skao.int/gms?prototyping-groups/mini-src/platform-users"
        # usersGroup: "ivo://cadc.nrc.ca/gms?skaha-users"
        adminsGroup: "ivo://cadc.nrc.ca/gms?skaha-admins"
        # The Resource ID of the Service that contains the Posix Mapping information
        posixMapperResourceID: "ivo://espsrc.iaa.csic.es/posix-mapper"
        registryURL: https://spsrc27.iaa.csic.es/reg
        # Resources provided to the Skaha service.
        resources:
        requests:
            memory: "550M"
            cpu: "500m"
        limits:
            memory: "550M"
            cpu: "500m"

        homeDir: "/arc/home"
        defautlQuotaGB: "10"
        # Optionally mount a custom CA certificate
        extraVolumeMounts:
        priorityClassName: uber-user-preempt-high
        serviceAccountName: skaha
        extraVolumes:

    secrets:

    storage:
    service:
        spec:
        persistentVolumeClaim:
            claimName: skaha-pvc 

Then install the `skaha` component:

.. code-block:: bash

    helm upgrade --install -n skaha-system --values skaha.yaml skaha science-platform/skaha 


Science portal
^^^^^^^^^^^^^^

Create a `science-portal.yaml` file with the next configuration:

.. warning::
   Change `<HOSTNAME>` according to your setup.
   Change `clientID` and `clientSecret` with the values of your IAM client. 

.. code-block:: bash

    # Tell Kubernetes to spin up multiple instances.  Defaults to 1.
    replicaCount: 1

    # It's best to keep these set as such, unless you're willing to change these in several places.
    skaha:
    namespace: skaha-system
    deployment:
    hostname: <HOSTNAME> # Change this!
    sciencePortal:
        image: images.opencadc.org/platform/science-portal:0.2.1
        imagePullPolicy: Always

        resources:
        requests:
            memory: "500M"
            cpu: "500m"
        limits:
            memory: "500M"
            cpu: "500m"
        # OIDC (IAM) server configuration.  These are required
        oidc:
        # Location of the OpenID Provider (OIdP), and where users will login
        uri: https://ska-iam.stfc.ac.uk/

        # The Client ID as listed on the OIdP.  Create one at the uri above.
        clientID:  <REDACTED>
        # The Client Secret, which should be generated by the OIdP.
        clientSecret: <REDACTED>
        #clientSecret: ALN-67opkQNhLUHtlrFfy6PlI6X_5iMivoBU3iFE05I34-VgzQA31veY5u8FREvtVNfOAIuPeAZVasWQDEu4oUA
        # Where the OIdP should send the User after successful authentication.  This is also known as the redirect_uri in OpenID.  This URI NEEDS
        redirectURI: https://<HOSTNAME>/science-portal/oidc-callback
        # Where to redirect to after the redirectURI callback has completed.  This will almost always be the URL to the /science-portal main page (https://example.com/science-portal).
        callbackURI: https://<HOSTNAME>/science-portal/
        # The standard OpenID scopes for token requests.  This is required, and if using the SKAO IAM, can be left as-is.
        scope: "openid profile offline_access"
        # The Resource ID of the Service that contains the URL of the Skaha service in the IVOA Registry
        skahaResourceID: ivo://espsrc.iaa.csic.es/skaha
        gmsID: ivo://skao.int/gms
        #gmsID: http://spsrc25.iaa.csic.es:18023
        registryURL: https://spsrc27.iaa.csic.es/reg
        identityManagerClass: org.opencadc.auth.StandardIdentityManager
        # The logo in the top left.  No link associated, just the image.  This can be relative, or absolute.
        # Default is the SRCNet Logo.
        #logoURL: /science-portal/images/SRCNetLogo.png


Then install the ``science-portal`` component`

.. code-block:: bash
    
    helm install -n skaha-system --values science-portal.yaml scienceportal science-platform/scienceportal


Cavern User Storage
^^^^^^^^^^^^^^^^^^^

Create a `cavern.yaml` file with the next configuration:

.. warning::
   Change `<HOSTNAME>` according to your setup, for example: ``canfar.espsrc.iaa.csic.es``. 

.. code-block:: bash

    # Skaha web service deployment
    deployment:
    hostname: <HOSTNAME>
    cavern:
        image: images.opencadc.org/platform/cavern:0.6.2
        imagePullPolicy: Always
        # How cavern identifies itself.
        resourceID: "ivo://espsrc.iaa.csic.es/cavern"

        registryURL: https://spsrc27.iaa.csic.es/reg
        # How to find the POSIX Mapper API.  URI (ivo://) or URL (https://).
        posixMapperResourceID: "ivo://espsrc.iaa.csic.es/posix-mapper"
        filesystem:
        # persistent data directory in container
        dataDir: "/data"

        # relative path to the node/file content that could be mounted in other containers, including Skaha.
        subPath: "/cavern"

        # See https://github.com/opencadc/vos/tree/master/cavern for documentation.  For deployments using OpenID Connect,
        # the rootOwner MUST be an object with the following properties set.
        rootOwner:
            # The adminUsername is required to be set whomever has admin access over the filesystem.dataDir above.
            adminUsername: mparra
            # The username of the root owner.
            username: mparra
            # The UID of the root owner.
            uid: 1000
            # The GID of the root owner.
            gid: 1000
        # Resources provided to the Skaha service.
        resources:
        requests:
            memory: "1Gi"
            cpu: "500m"
        limits:
            memory: "1Gi"
            cpu: "500m"

    # Set these appropriately to match your Persistent Volume Claim labels.
    storage:
    service:
        spec:
        # YAML for service mounted storage.
        # Example is the persistentV
        persistentVolumeClaim:
          claimName: skaha-pvc

Then install the `cavern` component:

.. code-block:: bash
    
    helm install -n skaha-system --values cavern.yaml cavern science-platform/cavern


Storage User Interface
^^^^^^^^^^^^^^^^^^^^^^


Create a `storage-ui.yaml` file with the next configuration:

.. warning::
   Change `<HOSTNAME>` according to your setup.
   Change `clientID` and `clientSecret` with the values of your IAM client. 
   Change `resourceID` with your `<IVO HOSTNAME>`.
   Change `nodeURIPrefix` with your `<IVO HOSTNAME>`.


.. code-block:: bash

    deployment:
    hostname: <HOSTNAME>
    storageUI:
        image: images.opencadc.org/client/storage-ui:1.1.0
        imagePullPolicy: Always

        # Resources provided to the Skaha service.
        resources:
        requests:
            memory: "500M"
            cpu: "500m"
        limits:
            memory: "500M"
            cpu: "500m"

        # Dictionary of all VOSpace APIs (Services) available that will be visible on the UI.
        # Format is:
        backend:
        defaultService: manucavern
        services:
            manucavern:
            resourceID: "ivo://<IVO HOSTNAME>/cavern"
            nodeURIPrefix: "vos://<IVO HOSTNAME>~cavern"
            userHomeDir: "/home"
            features:
                batchDownload: false
                batchUpload: false
                externalLinks: false
                paging: false

        # ID (URI) of the GMS Service.
        gmsID: ivo://skao.int/gms

        oidc:
        # Location of the OpenID Provider (OIdP), and where users will login
        uri: https://ska-iam.stfc.ac.uk/

        # The Client ID as listed on the OIdP.  Create one at the uri above.
        clientID:  <REDACTED>

        # The Client Secret, which should be generated by the OIdP.
        clientSecret: <REDACTED>

        # Where the OIdP should send the User after successful authentication.  This is also known as the redirect_uri in OpenID.  This URI NEEDS
        redirectURI: https://<HOSTNAME>/storage/oidc-callback

        # Where to redirect to after the redirectURI callback has completed.  This will almost always be the URL to the /science-portal main page (https://example.com/science-portal).
        callbackURI: https://<HOSTNAME>/storage/list

        # The standard OpenID scopes for token requests.  This is required, and if using the SKAO IAM, can be left as-is.
        scope: "openid profile offline_access"
        registryURL: https://spsrc27.iaa.csic.es/reg

        # The IdentityManager class handling authentication.  This should generally be left alone
        identityManagerClass: org.opencadc.auth.StandardIdentityManager

        # Default theme is the SRC one.
        themeName: src

    # For the token caching
    redis:
    architecture: 'standalone'
    auth:

Then install the `storage-ui` component:

.. code-block:: bash

    helm -n skaha-system upgrade --install --values storage-ui.yaml storage-ui science-platform-client/storageui



Post-Deployment Verification
----------------------------

In order for the services to work, the data of the deployed services must have been included in the CADC Registry. To check it access to https://spsrc27.iaa.csic.es/reg/#/
 then validate if your SRC is set there.

All CANFAR services by default are exposed through ``traefik``, so these services hang from ``/``, so you need to validate that you have access to the following:

- https://canfar.espsrc.iaa.csic.es/science-platform
- https://canfar.espsrc.iaa.csic.es/shaka/
- https://canfar.espsrc.iaa.csic.es/posix-mapper
- https://canfar.espsrc.iaa.csic.es/cavern

You must configure your ``host`` in all the deployments files for the services to enable the access to the current ``traefik``.


Troubleshooting
---------------

Validate pods logs
^^^^^^^^^^^^^^^^^^

To solve problems with CANFAR the first thing to check is the logs of each of the services to do this it will be necessary to check:

.. code-block:: bash

    $ kubectl get pods -n skaha-system

    NAME                                     READY   STATUS    RESTARTS      AGE
    posix-mapper-postgres-65c87b7cfb-jp877   1/1     Running   1 (26d ago)   122d
    storage-ui-tomcat-85d9bd8b44-d27mb       1/1     Running   1 (26d ago)   122d
    cavern-tomcat-6675d6486b-wwq4b           1/1     Running   1 (26d ago)   122d
    skaha-tomcat-86cc9bcb9f-6plkj            1/1     Running   1 (26d ago)   122d
    scienceportal-redis-master-0             1/1     Running   1 (26d ago)   122d
    cavern-uws-postgres-59b68d7f55-wvvpz     1/1     Running   0             26d
    science-portal-tomcat-75c6969bf5-grpt6   1/1     Running   0             26d
    storage-ui-redis-master-0                1/1     Running   0             26d
    posix-mapper-tomcat-59c487cc5c-x7gtf     1/1     Running   2 (16h ago)   26d

Then check for pods:

.. code-block:: bash
    
    kubectl logs posix-mapper-tomcat-59c487cc5c-x7gtf -n skaha-system
    ...


and for the workloads:

.. code-block:: bash

    $ kubectl get pods -n skaha-workload

Then check for each pod deployed:

.. code-block:: bash
    
    kubectl logs skaha-notebook-raw-hckv0w1u-m5hjs -n skaha-workload
    ...


GMS connectivity
^^^^^^^^^^^^^^^^

Other types of errors come from accessing SKAO-IAM through GMS. This error only occurs 
when GMS has been down and is not providing service which causes CANFAR to not work. 
To solve this, contact the person responsible for GMS and check what is happening. 

Harbor certificates
^^^^^^^^^^^^^^^^^^^
^
CANFAR relies on an external Container Hub so connectivity to this Hub must be correct 
and certificates must be unexpired. When certificates are expired CANFAR does not work, 
as many services depend on the Hub. To solve this, the auto-renewal of SSL certificates 
must be integrated in the Harbor service.

Services in OpenCADC Registry
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If the host name has changed it is necessary to add the new host to the CADC Registration service. 
If this is not done the CANFAR services will not be able to access and discover the other services 
on which they may depend. For inclusion or modification it is necessary to modify the service registry in ``spsrc-si-globa`` , through the file:

.. code-block:: bash
    
    /home/gi-spsrc/software/global-si/config/reg/reg-resource-caps.properties 

and then restart the service:

.. code-block:: bash
    
    docker restart reg
