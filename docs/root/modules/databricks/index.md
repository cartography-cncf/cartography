# Databricks

Cartography supports workspace inventory and optional account-level inventory
for Databricks on AWS and GCP.

Account-level ingestion includes SCIM users, groups, service principals,
workspace assignments, federation policies, and workspace cloud
configurations such as credentials, storage, networks, encryption keys, VPC
endpoints, log delivery, and budgets. Cartography links these objects to
existing AWS and GCP resources in the graph.

Without account-level options, the module runs in workspace-only mode.

```{toctree}
config
schema
```
