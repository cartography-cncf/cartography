# Google Cloud Platform (GCP)

Cartography supports ingesting Google Cloud Platform resources, including:

- **Cloud Resource Manager**: Organizations, Folders, Projects
- **Compute**: Instances, VPCs, Subnets, Firewalls, Forwarding Rules, Network Interfaces
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

```{toctree}
config
artifact-registry
cloud-run
schema
```
