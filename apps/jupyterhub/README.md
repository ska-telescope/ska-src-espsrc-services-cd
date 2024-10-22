## How does the structure work?

- Kustomize: Uses kustomization.yaml files to group and manage resources, ensuring that FluxCD can apply configurations.
- HelmRelease: The HelmRelease configuration deploys JupyterHub using the official chart and the values.yaml file.
