# RunPod

```{toctree}
config
schema
```

The RunPod module ingests account-scoped infrastructure inventory from the RunPod API
v2. It uses `RunPodAccount` as the tenant and security boundary, with pods,
serverless endpoints, network volumes, templates, registry credentials, clusters, SSH
keys, and catalog data centers modeled as resources under that account.

Billing and cost-center data are intentionally out of scope for the first RunPod
module implementation.
