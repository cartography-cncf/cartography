# Databricks

Cartography supports workspace inventory and optional account-level inventory
for Databricks on AWS and GCP.

Account-level ingestion includes SCIM users, groups, service principals,
workspace assignments, federation policies, and workspace cloud
configurations such as credentials, storage, networks, encryption keys, VPC
endpoints, log delivery, and budgets. Cartography links these objects to
existing AWS and GCP resources in the graph.

Without account-level options, the module runs in workspace-only mode.

## Shared Object Labels

Workspace objects that expose object-level ACLs carry the shared
`DatabricksAclObject` label. This includes clusters, cluster policies, instance
pools, jobs, pipelines, SQL warehouses, serving endpoints, apps, and secret
scopes. The label lets `HAS_PERMISSION` relationships connect users, groups,
and service principals to any ACL-bearing object. It is not a standalone node
type.

Grantable Unity Catalog objects carry the shared `DatabricksSecurable` label.
This includes metastores, catalogs, schemas, tables, volumes, functions,
connections, storage credentials, external locations, and registered models.
The label provides a common target for `HAS_PRIVILEGE` relationships and is
not a standalone node type.

## Cross-Provider Connections

Databricks cloud configurations connect to existing AWS and GCP resources when
those resources are already present in the graph. These connections cover
storage buckets, IAM principals, service accounts, VPCs, subnets, security
groups, VPC endpoints, and encryption keys.

Git-backed Databricks repositories also connect to their source
`GitHubRepository` through `SOURCED_FROM` when the matching repository is
already present.

Notebooks are materialized only when referenced by a job task. Cartography
creates a lightweight, path-keyed node for each referenced notebook without
retrieving notebook content, permissions, or the complete workspace tree.

Databricks identities and resources use ontology labels such as `Tenant`,
`UserAccount`, `ServiceAccount`, `UserGroup`, `Database`, `ObjectStorage`, and
`NetworkAccessControl` so they participate in cross-provider queries.

```{toctree}
config
queries
schema
```
