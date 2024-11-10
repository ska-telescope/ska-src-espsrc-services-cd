.. _perfsonar-manual :

perfSONAR Service
=================

.. tip::
    
    espSRC Service endpoint: https://perfsonar.espsrc.iaa.csic.es 

The perfSONAR service is a network measurement toolkit designed to facilitate the monitoring, 
testing, and troubleshooting of network performance across diverse and distributed environments. 
Widely used by research and education networks, perfSONAR provides a standardized framework for 
measuring network metrics such as bandwidth, latency, packet loss, and jitter.

By deploying perfSONAR nodes across multiple sites, organizations can gain real-time insights 
into the health of their network infrastructure, detect performance bottlenecks, and optimize 
data transfer paths. This capability is particularly valuable for high-throughput scientific 
collaborations that rely on stable and efficient network connections, enabling researchers 
to ensure seamless data exchange across global research networks.

Prerequisites
-------------

DMZ and DTN
^^^^^^^^^^^

For our RSE this service has been implemented in an individual VM with internet access and within a DMZ. perfSONAR 
is primarily aiming to test the network between SRC sites. For this reason it is recommended 
to not place the host behind a proxy which could make the results more difficult to interpret. 
Moreover it makes installation and configuration of a perfSONAR host more difficult. If it is possible to still
place the perfSONAR host close to the DTN this is advised. 

.. note:: 
    
    If it is possible to still place the perfSONAR host close to the DTN this is advised.

Ports configuration
^^^^^^^^^^^^^^^^^^^

For this configuration it will be necessary to have access to the Firewall and to implement 
the necessary policies for port access from outside to inside and vice versa. There are a number 
of ports that need to be added to the firewall: 

.. list-table:: Ports
   :widths: 25 25 25 25
   :header-rows: 1

   * - Tool 
     - TCP ports
     - UDP ports
     - required for v0.1
   * - owamp (control)
     - 861
     - 
     - ✓
   * - owamp (test)
     - 
     - 8760-9960
     - ✓
   * - twamp (control)
     - 862
     - 
     - 
   * - twamp (test)
     - 
     - 18760-19960
     - 
   * - pscheduler 
     - 443 
     - 
     - ✓
   * - traceroute 
     - 
     - 33434-33634
     - 
   * - simplestream
     - 5890-5900
     - 
     - 
   * - nuttcp
     - 5000,5101
     - 
     - 
   * - iperf3
     - 5201
     - 
     - ✓
   * - iperf2
     - 5001
     - 
     - 
   * - ntp 
     - 
     - 123
     - 

.. important:: 
    
    It is also required that ICMP be enabled!

Before installation
^^^^^^^^^^^^^^^^^^^

perfSONAR has several bundles to choose from, ranging from tools (which is a basic collection of the 
monitoring tools listed above) to the toolkit which also includes the dashboard and archive modules. 

It is recommended to install the testpoint bundle (or container) as this is the most lightweight bundle with 
scheduling functionality. 


Deployment Steps and Service Configuration
------------------------------------------

Configure `apt` sources:

.. code-block:: bash

   curl -o /etc/apt/sources.list.d/perfsonar-release.list https://downloads.perfsonar.net/debian/perfsonar-release.list
   curl -s -o /etc/apt/trusted.gpg.d/perfsonar-release.gpg.asc https://downloads.perfsonar.net/debian/perfsonar-release.gpg.key

.. rubric:: Ubuntu only

Additionally, if you’re running a stripped-down Ubuntu installation, 
you might need to enable the universe repository. This is done with the following command:

.. code-block:: bash

   add-apt-repository universe


Then refresh the packages list so APT knows about the perfSONAR packages:

.. code-block:: bash

    apt update

Installation: 

.. code-block:: bash

    env OPENSEARCH_INITIAL_ADMIN_PASSWORD=perfSONAR123! apt install perfsonar-toolkit

During the installation process, you’ll be asked to choose a password for the pscheduler database.

You can start all the services by rebooting the host since all are configured to run by default. In order to check services status issue the following commands:

.. code-block:: bash

    service pscheduler-scheduler status
    service pscheduler-runner status
    service pscheduler-archiver status
    service pscheduler-ticker status
    service owamp-server status
    service perfsonar-lsregistrationdaemon status

If they are not running you may start them with appropriate service commands as a root user. For example:

.. code-block:: bash

    service pscheduler-scheduler start
    service pscheduler-runner start
    service pscheduler-archiver start
    service pscheduler-ticker start
    service owamp-server start
    service perfsonar-lsregistrationdaemon start

Note that you may have to wait a few hours for NTP to synchronize your clock before (re)starting owamp-server.

After installing the perfsonar-toolkit bundle, you can refer to the general perfSONAR 
configuration from https://docs.perfsonar.net/install_config_first_time.html


Post-Deployment Verification
----------------------------

Check that our host espSRC (``spsrc33.iaa.csic.es``) providing the access point to perfSONAR is included within the Grafana portal:

        https://perfsonar01.jc.rl.ac.uk/grafana

The central perfSONAR host also uses a configuration file to schedule tests between all hosts in the mesh:

        https://perfsonar01.jc.rl.ac.uk/psconfig/psconfig-test.json

Validate if ``spsrc33.iaa.csic.es`` is set in this file ``psconfig-test.json``.

Check local perfSONAR dashboard in Grafana: https://perfsonar.espsrc.iaa.csic.es. 

Troubleshooting
---------------

Aside from checking if the services are running, perfSONAR also has its own troubleshooter. 
This can also be used on external hosts: 

.. code-block:: bash

    pscheduler troubleshoot
    pscheduler troubleshoot --dest hostname

There are also tools perfSONAR can use to test for bandwidth, path, and latency using "throughput" (default iperf3)
, rtt (default ping), and "trace" (default traceroute). These tools have their own defaults 
, but these can be modified: 

.. code-block:: bash
    
    pscheduler task throughput --dest hostname
    pscheduler task trace --dest hostname
    pscheduler task rtt --dest hostname

By specifying a source node, you can also run tests between other hosts and direct tests to your own host for troubleshooting

.. code-block:: bash

    pscheduler task throughput --source hostname --dest hostname

This should help determine that your host is contactable. You can also schedule repeatable tests. To interrogate the scheduled tests
"monitor" will show an updating schedule. But "schedule" will help seeing past and upcoming tests
For example, the past 2 hours of the schedule can be shown by adding -PT2H

.. code-block:: bash

    pscheduler monitor
    pscheduler schedule -PT2H


