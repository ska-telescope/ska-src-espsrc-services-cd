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
 
espSRC Rucio RSE
----------------

WebDav deployment :doc:`./deployments/rse/manual` 

.. note::

  | EndPoint 1: https://spsrc14.iaa.csic.es:18027/disk
  |  Endpoint 2: https://rucio.espsrc.iaa.csic.es

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

