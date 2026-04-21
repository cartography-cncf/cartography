# Microsoft


```{toctree}
config
schema
```


The `microsoft` module is the top-level umbrella for Microsoft tenant, SaaS, and security control plane data ingested via Microsoft Graph. It includes:

- **entra** — Entra ID identity objects (users, groups, OUs, applications, service principals, app role assignments)
- **intune** — Intune managed devices, detected apps, and compliance policies

`microsoft` is the canonical top-level module name. `entra` remains accepted as a backward-compatible alias for module selection and ontology source configuration during the migration.

Supports commercial, GCC High / DoD (US Government), and China sovereign clouds — see [config](config) for details.
