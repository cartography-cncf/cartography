# Amazon Web Services (AWS)

Cartography supports both single-account and multi-account AWS syncs. Resource
inventory is synced per account. AWS Organizations hierarchy ingestion is a
separate best-effort step that models organizations, roots, organizational
units, and account placement.

For reliable hierarchy ingestion, include credentials for the Organizations
management account or a delegated administrator account. If Cartography cannot
enumerate a complete hierarchy, it preserves previous hierarchy data by
skipping Organizations cleanup while continuing account resource sync.

```{toctree}
config
permissions-mapping
organizations
infrastructure-investigations
container-images
identity-access
tagging-and-labels
schema
```
