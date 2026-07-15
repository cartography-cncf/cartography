# Microsoft


```{toctree}
config
schema
examples
analysis
```


The `microsoft` module is the top-level umbrella for Microsoft tenant, SaaS, and security control plane data ingested via Microsoft Graph. It includes:

- **entra**: Entra ID identity objects (users, groups, OUs, applications, service principals, and app role assignments)
- **intune**: Intune managed devices, detected apps, and compliance policies

`microsoft` is the canonical top-level module name. `entra` remains accepted as a backward-compatible alias for module selection and ontology source configuration during the migration.

Microsoft and Azure ingestion share `AzureTenant` as the primary tenant node. Microsoft Graph ingestion also adds the `EntraTenant` compatibility label to that node.

See the [configuration docs](config.md), [schema](schema.md), [example queries](examples.md), and [analysis behavior](analysis.md) for details.
