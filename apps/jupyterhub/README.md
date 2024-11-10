# JupyterHub deployment on FluxCD

## FluxCD is working: Suspend fluxcd actions

```
flux get kustomizations
flux get sources git
flux get helmreleases -A

flux suspend kustomization flux-system
flux suspend helmrelease jupyterhub -n jupyterhub-test
flux suspend source git flux-system
flux suspend source helm jupyterhub-repository
flux suspend source chart jupyterhub-test-jupyterhub
```


## Activate JupyterHub Policy for Vault

Connect to the vault pods:

```
kubectl exec -it vault-0 -n vault -- /bin/sh
```

Create path for the apps: `app` with type `kv-v2` and add the auth for Kubernetes and vault:

```
vault secrets enable -path=apps kv-v2
vault auth enable kubernetes
vault write auth/kubernetes/config kubernetes_host="https://kubernetes.default.svc"
```


Create the Key-Values (KVs) you need. For JupyterHub we defined the next 3 keys:

```
vault kv put app/jupyter client-id=""
vault kv put app/jupyter client-secret=""
vault kv put app/jupyter token=""
```

Create a policy for JupyterHub. In this case for all the paths:

```
vi jupyterhub_policy.hcl

path "*" {
  capabilities = ["read"]
}
```

Or if you want a more fine grain, just add the route to the path itself:

```
vi jupyterhub_policy.hcl

path "app/data/jupyter" {
  capabilities = ["read"]
}
```

Note: Add ``/data/`` to your path even you added your KV as ````app/jupyter``

Then write this policy:

```
vault policy write jupyter-policy /tmp/jupyter_policy.hc`
```

And finally associate the role (``auth/kubernetes/role/jupyterhub``) to the policy (``jupyter-policy``) and both to the ``Service Account`` and the ``Service Account Namepsace``:

```
vault write auth/kubernetes/role/jupyterhub bound_service_account_names=jupyterhub  bound_service_account_namespaces=jupyterhub-test policies=jupyter-policy ttl=24h
```

### Validations

Vault level:

```
vault kv get app/jupyter
```

Kubernetes cluster level:

```
kubectl describe secret -n jupyterhub-test
```

You will see:
```
... 
Data
====
CLIENT-ID:  36 bytes
CLIENT-SECRET: 128 bytes
TOKEN: 32 byres
```