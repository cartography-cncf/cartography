# Google Cloud Platform (GCP)

Cartography supports ingesting Google Cloud Platform resources, including:

- **Cloud Resource Manager**: Organizations, Folders, Projects
- **Compute**: Instances, VPCs, Subnets, Firewalls, Forwarding Rules, Network Interfaces, SSL Policies, Target HTTPS Proxies, Target SSL Proxies, VPC Peerings, VPN Gateways, VPN Tunnels
- **Storage**: Buckets
- **DNS**: Zones, Record Sets
- **IAM**: Service Accounts, Roles, Policy Bindings
- **Bigtable**: Instances, Clusters, Tables, App Profiles, Backups
- **Google Kubernetes Engine (GKE)**: Clusters
- **Vertex AI**: Models, Endpoints, Deployed Models, Workbench Instances, Training Pipelines, Feature Groups, Datasets
- **Cloud SQL**: Instances, Databases, Users, Backup Configurations
- **BigQuery**: Datasets, Tables, Routines, Connections
- **Secret Manager**: Secrets, Secret Versions
- **Cloud Run**: Services, Revisions, Jobs, Executions

## VPC peerings and VPN tunnels

VPC peerings are extracted from each network's `peerings` field (no extra API
call) and modeled as `GCPVpcPeering` nodes linked to the local VPC via
`LOCAL_NETWORK`. When the peer network belongs to a project that has not been
synced, Cartography creates a `GCPVpc` stub node so the `PEER_NETWORK`
relationship still resolves.

VPN tunnels (`GCPVpnTunnel`) and VPN gateways (`GCPVpnGateway`) are fetched
with the Compute aggregated list endpoints (one request chain per project,
with partial success enabled; cleanup is skipped whenever any region scope
returns an error). Gateways are synced before tunnels so that `USES_GATEWAY`
relationships resolve in the same sync cycle; peer gateways outside the synced
project are represented as stub nodes linked via `CONNECTS_TO_GATEWAY`.

Stub nodes are reference-counted by their relationships, not by a sync scope:
once no peering or tunnel references a stub (and no synced project owns it),
it is removed automatically on the next sync.

## Cloud Asset Inventory behavior

Cartography uses the Cloud Asset Inventory API as a fallback for service
accounts and project-level custom roles when the IAM API is disabled on a
project. It also uses Cloud Asset Inventory to sync effective IAM policy
bindings, including policies inherited from organizations and folders.

Permission relationship syncs depend on policy bindings from the current run.
If Cloud Asset Inventory is unavailable or the Cartography identity lacks
`roles/cloudasset.viewer`, Cartography skips those relationships for the
affected project. Other resource syncs continue.

The fallback covers service accounts and project-level custom roles. Predefined
roles and organization-level custom roles are synced separately through the IAM
API.

## BigQuery permission grains

A permission relationship on a `GCPBigQueryTable` means an IAM binding placed
**directly on that table**. Grants held at the project, folder, organization or
dataset level are not expanded into one relationship per table: they land on the
`GCPBigQueryDataset` and reach the tables through `HAS_TABLE`. Nothing table-level
is consulted when evaluating them (no table ACL, no row or column level security,
no authorized view), so expanding them per table added no information while writing
millions of relationships on large projects.

Query effective access as the union of the two grains:

```cypher
MATCH (p:GCPPrincipal)-[:CAN_READ]->(t:GCPBigQueryTable)
RETURN p.email AS principal, t.id AS table, 'table binding' AS grain
UNION
MATCH (p:GCPPrincipal)-[:CAN_READ]->(:GCPBigQueryDataset)-[:HAS_TABLE]->(t:GCPBigQueryTable)
RETURN p.email AS principal, t.id AS table, 'dataset grant' AS grain
```

Each relationship carries its own `has_condition`, `condition_title` and
`condition_expression`, so a conditional binding on one table and an unconditional
grant on its dataset are both represented, each on its own grain.

```{toctree}
config
artifact-registry
cloud-run
permission-mapping
schema
```
