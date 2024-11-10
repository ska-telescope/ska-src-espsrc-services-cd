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
  :width: 750
  :alt: RSE header image


The espSRC is integrated as a RSE (Rucio Storage Element) within the SKAO Rucio data lake. 
The RSE deployment of the espSRC consists of a VM that mounts to a CephFS-based mass storage space. 
The implementation used for the RSE within the espSRC is based on WebDav, specifically the StoRM-WebDav setup (manual and helm [on kubernetes]).
Currently the service is connected through a proxy that redirects requests from users to the service itself.

- StoRM-WebDav deployment - Manual :doc:`./deployments/rse/manual` , versión of StoRM WebDav: 1.4
- StoRM-WebDav deployment - Helm :doc:`./deployments/rse/helm` , versión of StoRM WebDav: 1.6
- Installation reproducibility: |:white_check_mark:| Manual and |:warning:| Helm (in progress)
- Storage size: **10TB**
- Integrations: 
   | |:white_check_mark:| SKAO-IAM - `Client SKAO-IAM <https://ska-iam.stfc.ac.uk/dashboard#!/home/clients>`_
   | |:white_check_mark:| SKAO Data lake  
   | |:white_check_mark:| Site Capabilities 
   | |:white_check_mark:| Functional tests
   | |:white_check_mark:| SKAO Rucio Monitoring system

Endpoints for this service: 

.. note::

  | EndPoint 1: https://spsrc14.iaa.csic.es:18027/disk
  | (|:warning:|) Endpoint 2: https://rucio.espsrc.iaa.csic.es - in progress


.. toctree::
  :caption: Jupyter
  :maxdepth: 2
  :hidden:
  
  deployments/jupyter/helm
 
JupyterHub
----------

JupyterHub provides interactive and collaborative notebook environment. 

- Indicar:
  - Instalado en Kubernets : en prod y Dev.
  - Integraciones: IAM y RSE (para Dev)
  - Esquema de Servicios graficamente.
  - Pre-configuración de HAproxy 

Helm deployment :doc:`./deployments/jupyterhub/helm`

.. note::

  EndPoint: https://notebook.espsrc.iaa.csic.es


SODA Service
------------
Docker deployment :doc:`./deployments/soda/docker`. 

GateKeeper Service
------------
Helm deployment :doc:`./deployments/gatekeeper/helm`. 

PerfSONAR Service
-----------------
Deployment :doc:`./deployments/perfsonar/manual`. 

Local Monitoring Service
------------------------
Deployment :doc:`./deployments/monitoring/docker`. 

PrepareData Service
-------------------
Deployment :doc:`./deployments/preparedata/docker`. 

CANFAR Science Platform
----------
Helm deployment :doc:`./deployments/canfar/helm`. 

