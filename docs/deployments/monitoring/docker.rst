.. _localmonitoring-docker :

Monitoring - Docker
========================

.. tip::
    
    espSRC Service endpoint: https://monitor.espsrc.iaa.csic.es 

The Local Monitoring Service leverages Prometheus and Grafana to monitor 
system metrics and service availability in local environments. Prometheus 
collects data from servers and applications using Node Exporter for hardware 
and system-level metrics, and Blackbox Exporter for probing endpoints to check 
availability and latency of local services.

Grafana connects to Prometheus as a data source to provide 
real-time visualization of these metrics through customizable dashboards. 
This integrated setup enables proactive monitoring, helping to quickly 
identify and resolve performance issues, ensuring optimal infrastructure reliability and efficiency.


Prerequisites
-------------



Service Configuration and Deployment Steps
------------------------------------------

Create a ``values.yaml`` configuration file and change the external port ``EXTERNAL_PORT1-2-3`` with the corresponding ports.

.. code-block:: bash

    version: '3.7'
    services:
    prometheus:
        image: prom/prometheus:latest
        container_name: prometheus
        volumes:
        - ./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
        - ./prometheus/data:/prometheus
        ports:
        - "EXTERNAL_PORT1:9090"
        command:
        - '--config.file=/etc/prometheus/prometheus.yml'
        - '--storage.tsdb.path=/prometheus'
        - '--storage.tsdb.retention.time=1y'
    
    grafana:
            #image: grafana/grafana:latest
        image: grafana/grafana-enterprise:11.2.0-ubuntu
        container_name: grafana
        environment:
        - GF_PATHS_PROVISIONING=/etc/grafana/provisioning
        - GF_SERVER_ROOT_URL=<SERVER ROOT>
        volumes:
        - ./grafana/grafana.ini:/etc/grafana/grafana.ini
        - ./grafana/data:/var/lib/grafana
        ports:
        - "EXTERNAL_PORT2:3000"
    
    blackbox_exporter:
        image: prom/blackbox-exporter:latest
        container_name: blackbox_exporter
        volumes:
        - ./blackbox_exporter/blackbox.yml:/etc/blackbox_exporter/config.yml
        ports:
        - "EXTERNAL_PORT3:9115"
        command:
        - '--config.file=/etc/blackbox_exporter/config.yml'


Then create the config files for ``prometheus.yml``, with the next: 

.. code-block:: bash

    global:
    scrape_interval: 120s
 
    scrape_configs:
    - job_name: 'prometheus'
        static_configs:
        - targets: ['localhost:EXTERNAL_PORT1']
    
    - job_name: 'blackbox'
        metrics_path: /probe
        params:
        module: [http_2xx]
        static_configs:
        - targets: # ADD HERE THE URL OF YOUR SERVICES AS MANY AS YOU WANT TO MONITOR
            - https://spsrc25.iaa.csic.es
            - <OTHER SERVICES>
        relabel_configs:
        - source_labels: [__address__]
            target_label: __param_target
        - source_labels: [__param_target]
            target_label: instance
        - target_label: __address__
            replacement: blackbox_exporter:9115

Change/add services you want to monitor by checking http `2XX`. In this example we've added ``https://spsrc25.iaa.csic.es``, but it can be any local or external service by adding new URLs in ``<OTHER SERVICES>``.

Then create the config files for ``grafana.yml``, with the next: 

.. code-block:: bash

    [server]
    #http_port = 3000 # if you need to use a specific port
    root_url = <SERVICE URL>
    
    [security]
    admin_user = admin
    admin_password = <YOUR_PASSWORD>
    
    [auth]
    oauth_allow_insecure_email_lookup=true
    
    # The following configuration is to use SKAO IAM service
    [auth.generic_oauth]
    enabled = true
    name = "IAM Provider"                 # Name in the button in login page
    allow_sign_up = true                  # Allowing new users to register
    client_id = <CLIENT ID>            # IAM client id
    client_secret = <CLIENT SECRET>    # Client password
    scopes = openid profile email         # Scopes
    auth_url = https://ska-iam.stfc.ac.uk/authorize  #
    token_url = https://ska-iam.stfc.ac.uk/token #
    api_url = https://ska-iam.stfc.ac.uk/userinfo #
    redirect_uri = https://your.domain.com/login/generic_oauth 

Change ``<SERVICE URL>`` with the ``URL`` of your grafana service endpoint. Add a password for the `admin` account in ``<YOUR_PASSWORD>`` and
include a ``<CLIENT ID>`` and ``<CLIENT SECRET>`` with the values of an SKA IAM client that you have previously created.

Finally run:

.. code-block:: bash

    docker compose up -d

In order to be able to visualise the metrics in Grafana of the exposed services, 
it is necessary to install a Grafana dashboard that has a predefined interface for 
this purpose. Dashboard. A dashboard can be selected to test and check the metrics:

- Blackbox Exporter (HTTP prober) https://grafana.com/grafana/dashboards/13659-blackbox-exporter-http-prober/
- Overview of Blackbox Exporter: https://grafana.com/grafana/dashboards/5345-blackbox-exporter-overview/

Post-Deployment Verification
----------------------------

TBC


Troubleshooting
---------------

TBC
