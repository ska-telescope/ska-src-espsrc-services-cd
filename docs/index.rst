.. espSRC docs

espSRC Services Deployment
==========================


.. toctree::
   :hidden:

   self


.. toctree::
  :caption: Rucio RSE
  :maxdepth: 2
  :hidden:

  
  deployments/rse/manual
  deployments/rse/helm
 
espSRC Rucio RSE
----------------

.. image:: _static/rse.png
  :width: 780
  :alt: RSE header image



The espSRC is integrated as a RSE (Rucio Storage Element) within the SKAO Rucio data lake. 
The RSE deployment of the espSRC consists of a VM that mounts to a CephFS-based mass storage space. 
The implementation used for the RSE within the espSRC is based on WebDav, specifically the StoRM-WebDav setup (manual and helm [on kubernetes]).
Currently the service is connected through a proxy that redirects requests from users to the service itself.

- StoRM-WebDav deployment - Manual :doc:`./deployments/rse/manual` , version of StoRM WebDav: 1.4
- StoRM-WebDav deployment - Helm :doc:`./deployments/rse/helm` , version of StoRM WebDav: 1.4
- Installation reproducibility: |:white_check_mark:| Manual and |:warning:| Helm (in progress)
- Storage size: **10TB**
- Integrations: 
   | |:white_check_mark:| SKAO-IAM - `Client SKAO-IAM <https://ska-iam.stfc.ac.uk/dashboard#!/home/clients>`_
   | |:white_check_mark:| SKAO Data lake  
   | |:white_check_mark:| Site Capabilities 
   | |:white_check_mark:| Functional tests
   | |:white_check_mark:| SKAO Rucio Monitoring system

**Endpoints for this service:**

.. note::

  | EndPoint 1: https://spsrc14.iaa.csic.es:18027/disk
  | (|:warning:|) Endpoint 2: https://rucio.espsrc.iaa.csic.es - in progress


.. toctree::
  :caption: JupyterHub
  :maxdepth: 2
  :hidden:
  
  deployments/jupyter/helm
  deployments/jupyter/gitops
 
JupyterHub
----------

.. image:: _static/jupyter.png
  :width: 780
  :alt: Jupyter RSE header image


JupyterHub provides an interactive and collaborative notebook environment for doing science in a very dynamic 
and visual way. It offers a complete working environment that supports any customisation of programming languages, 
access to a console and scalable computing power. The espSRC is deployed within a Kubernetes cluster (one for production 
and one for development) and a notebooks service with JupyterHub. Access to this service is provided through a HAProxy 
load balancing service. The storage provisioning model of the user accounts is carried out through a StorageClass with a CephFS backend. 
For the production notebooks service, the Rucio Storage Element of the espSRC storage has not been set up, but for the development cluster, 
the RSE has been set up for testing purposes. 

- StoRM-WebDav deployment - Helm :doc:`./deployments/jupyter/helm` , version of JupyterHub: 3.1.0
- StoRM-WebDav deployment - via GitOps :doc:`./deployments/jupyter/gitops` , version of StoRM WebDav: 1.4
- Installation reproducibility: |:white_check_mark:| Helm and |:white_check_mark:| GitOps 
- Storage size for users: **1TB** (extendable)
- Integrations: 
   | |:white_check_mark:| SKAO-IAM - `Client SKAO-IAM <https://ska-iam.stfc.ac.uk/dashboard#!/home/clients>`_
   | |:white_check_mark:| Site Capabilities
   | |:white_check_mark:| Access/Mounted espSRC RSE for the development cluster (https://dev-notebook.espsrc.iaa.csic.es)

**Endpoints for this service:**

.. note::

  | EndPoint: https://notebook.espsrc.iaa.csic.es
  | EndPoint development: https://dev-notebook.espsrc.iaa.csic.es




.. toctree::
  :caption: SODA Service
  :maxdepth: 2
  :hidden:
  
  deployments/soda/docker
  deployments/soda/helm


SODA Service
------------

Server-side Operations for Data Access (SODA) is a low-level data access capability and a server side data processing 
that can act upon the data files, performing various kinds of operations: filtering/subsection, transformations, pixel 
operations, and applying several other functions to the data. As part of SRCNet 0.1, this service is provided locally
within the SRC and will not be exposed like others. Additional external services may make use of the SODA service 
through e.g. the GateKeeper service (see description and installation). This deployment is currently running on a VM 
that is and the load balancing service is in charge of exposing the service externally/locally. 

- VisIVO SODA - Docker :doc:`./deployments/soda/docker` , version of VisIVO Soda Server: 1.6.0
- VisIVO SODA - Helm :doc:`./deployments/soda/helm` , version of VisIVO Soda Server: 1.7.0
- Installation reproducibility: |:white_check_mark:| Docker and |:warning:| Helm (in progress)
- Storage size: Same of the espSRC RSE (10TB)
- Integrations: 
   | |:white_check_mark:| SKAO-IAM - `Client SKAO-IAM <https://ska-iam.stfc.ac.uk/dashboard#!/home/clients>`_
   | |:white_check_mark:| Site Capabilities
   | |:white_check_mark:| Access/Mounted espSRC RSE. 

**Endpoint for this service:**

.. note::

  | EndPoint: https://soda.espsrc.iaa.csic.es (currently exposed externally)

.. GateKeeper documentation start point 
  --------------------------------------------

.. toctree::
  :caption: GateKeeper
  :maxdepth: 2
  :hidden:
  
  deployments/gatekeeper/helm

GateKeeper Service
------------
Helm deployment :doc:`./deployments/gatekeeper/helm`. 

.. PerfSONAR documentation start point 
  --------------------------------------------

.. toctree::
  :caption: PerfSONAR
  :maxdepth: 2
  :hidden:
  
  deployments/perfSONAR/manual

PerfSONAR Service
-----------------
Deployment :doc:`./deployments/perfsonar/manual`. 


.. Local Monitoring documentation start point 
  --------------------------------------------

.. toctree::
  :caption: Local monitoring
  :maxdepth: 2
  :hidden:
  
  deployments/monitoring/docker

Local Monitoring Service
------------------------
Deployment :doc:`./deployments/monitoring/docker`. 

PrepareData Service
-------------------
Deployment :doc:`./deployments/preparedata/docker`. 

CANFAR Science Platform
----------
Helm deployment :doc:`./deployments/canfar/helm`. 

