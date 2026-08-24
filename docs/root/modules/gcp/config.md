# GCP Configuration

## Prerequisites

Create a Google Cloud user account or service account for Cartography. Identify
the project that hosts the service account because Google bills API calls to
that host project.

Enable the required APIs on the host project:

```bash
gcloud services enable cloudresourcemanager.googleapis.com --project=YOUR_HOST_PROJECT
gcloud services enable serviceusage.googleapis.com --project=YOUR_HOST_PROJECT
gcloud services enable iam.googleapis.com --project=YOUR_HOST_PROJECT
```

## Authentication

Cartography uses Google Application Default Credentials. Use either method:

### Credential file

Set `GOOGLE_APPLICATION_CREDENTIALS` to a JSON credential file. Restrict file
read access to the Cartography user.

```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/credentials.json"
```

### Attached service account

When Cartography runs on Google Compute Engine or another Google Cloud service,
use the service account attached to that runtime.

## Required Permissions

Grant these roles to the Cartography identity at the organization level:

| Role | Purpose |
|------|---------|
| `roles/iam.securityReviewer` | List and get IAM roles, service accounts, and Workload Identity Federation pools and providers |
| `roles/compute.viewer` | List and get Compute Engine inventory, including instances, networking, SSL policies, and target proxies |
| `roles/resourcemanager.organizationViewer` | List and get Google Cloud organizations |
| `roles/resourcemanager.folderViewer` | List and get Google Cloud folders |

To grant a role:

```bash
gcloud organizations add-iam-policy-binding YOUR_ORG_ID \
  --member="user:YOUR_EMAIL_OR_SERVICE_ACCOUNT" \
  --role="ROLE_NAME"
```

Find the organization ID with:

```bash
gcloud organizations list
```

If you use a custom role instead of `roles/iam.securityReviewer`, include
`iam.workloadIdentityPools.list` and
`iam.workloadIdentityPoolProviders.list`, or also grant
`roles/iam.workloadIdentityPoolViewer`.

## Optional Permissions

Grant only the roles needed for the resource types you want to sync:

| Role | Purpose |
|------|---------|
| `roles/bigquery.dataViewer` | List and get BigQuery datasets, tables, and routines |
| `roles/bigquery.connectionUser` | List BigQuery connections |
| `roles/cloudasset.viewer` | Sync effective IAM policy bindings and permission relationships that depend on them |
| `roles/artifactregistry.reader` | List and get Artifact Registry repositories and artifacts |
| `roles/run.viewer` | List and get Cloud Run services, jobs, and executions |
| `roles/notebooks.viewer` | List and get Vertex AI Workbench resources |
| `roles/serviceusage.apiKeysViewer` | List and get Google Cloud API keys |

Enable optional APIs on the host project according to the resources you want
to sync:

```bash
gcloud services enable compute.googleapis.com --project=YOUR_HOST_PROJECT
gcloud services enable storage.googleapis.com --project=YOUR_HOST_PROJECT
gcloud services enable container.googleapis.com --project=YOUR_HOST_PROJECT
gcloud services enable dns.googleapis.com --project=YOUR_HOST_PROJECT
gcloud services enable cloudkms.googleapis.com --project=YOUR_HOST_PROJECT
gcloud services enable bigtableadmin.googleapis.com --project=YOUR_HOST_PROJECT
gcloud services enable sqladmin.googleapis.com --project=YOUR_HOST_PROJECT
gcloud services enable bigquery.googleapis.com --project=YOUR_HOST_PROJECT
gcloud services enable bigqueryconnection.googleapis.com --project=YOUR_HOST_PROJECT
gcloud services enable cloudfunctions.googleapis.com --project=YOUR_HOST_PROJECT
gcloud services enable secretmanager.googleapis.com --project=YOUR_HOST_PROJECT
gcloud services enable artifactregistry.googleapis.com --project=YOUR_HOST_PROJECT
gcloud services enable run.googleapis.com --project=YOUR_HOST_PROJECT
gcloud services enable aiplatform.googleapis.com --project=YOUR_HOST_PROJECT
gcloud services enable notebooks.googleapis.com --project=YOUR_HOST_PROJECT
gcloud services enable cloudasset.googleapis.com --project=YOUR_HOST_PROJECT
gcloud services enable apikeys.googleapis.com --project=YOUR_HOST_PROJECT
```

## Configure Cartography

No module-specific option is required when Application Default Credentials are
available. If you set `GOOGLE_CLOUD_QUOTA_PROJECT`, enable the same APIs on that
quota project. The host project and quota project are typically the same.

To sync Cloud Asset Inventory policy bindings, enable its API on the service
account host project and grant `roles/cloudasset.viewer` at the organization
level:

```bash
gcloud services enable cloudasset.googleapis.com --project=YOUR_SERVICE_ACCOUNT_PROJECT
```

## Run Cartography

```bash
cartography --selected-modules gcp
```

## Syncing specific projects without an organization

By default Cartography discovers GCP Organizations the identity can access and syncs every project beneath them. If you only want to sync one or more specific projects — for testing, or because the project does not belong to a GCP Organization, or because you only have project-scoped credentials — pass `--gcp-project-ids` with a comma-separated list of project IDs:

```bash
cartography --gcp-project-ids my-project-1,my-project-2
```

When `--gcp-project-ids` is set, Cartography:

- Fetches exactly those projects directly (no organization or folder discovery).
- Syncs each project's resources (Compute, IAM, Storage, etc.), honouring `--gcp-requested-syncs` if also provided.
- Creates a `(:GCPProject)-[:PARENT]->(:GCPOrganization|:GCPFolder)` edge only if the parent node already exists in the graph (for example from a prior full org-based sync).

Notes and limitations of this mode:

- An inaccessible or non-existent project ID is logged and skipped rather than aborting the whole run, so the remaining project IDs still sync. Projects that exist but are not `ACTIVE` (for example, pending deletion) are likewise skipped with a warning rather than ingested. (Transient API errors are not skipped and will still fail the sync.)
- Organization-level data is **not** synced: GCP Organizations, Folders, and inherited (org/folder) policy bindings are skipped. Project-level resources and bindings are synced normally.
- Google **predefined** roles (`roles/owner`, `roles/editor`, ...) are synced: they are global and need no organization access, so their `GCPRole` nodes are loaded (letting `(:GCPPolicyBinding)-[:GRANTS_ROLE]->(:GCPRole)` edges form) and their permissions expand into permission relationships. These predefined `GCPRole` nodes are not cleaned up in this mode (a global cleanup would delete role nodes synced by the org-based path). Organization-level **custom** roles, however, are **not** synced in this mode (they require organization access), so any policy binding that references an org custom role will not link to a role node or expand into permission relationships.
- The `GCPProject` node is not cleaned up by this mode (there is no organization to scope a cleanup against). Resources within each synced project are still cleaned up normally, scoped to the project.

## Advanced Configuration

| CLI flag | Description |
|----------|-------------|
| `--gcp-requested-syncs` | Comma-separated GCP resources to sync, such as `compute,iam,storage` |
| `--gcp-permission-relationships-file` | Path to the GCP permission relationship mapping file |
| `--gcp-project-ids` | Comma-separated GCP project IDs to sync directly, bypassing organization and folder discovery |

## Troubleshooting

- If an API is not enabled on the host or quota project, Cartography logs a
  warning and skips that resource type.
- Some services emit per-location permission warnings. Cartography skips only
  the affected locations.
- Without the Workload Identity Federation permissions listed above,
  Cartography logs a 403 warning and does not populate
  `GCPWorkloadIdentityPool` or `GCPWorkloadIdentityProvider` nodes.
- Cloud Asset Inventory fallback requires its API on the service account host
  project. Policy binding sync also requires organization-level
  `roles/cloudasset.viewer`.
- Permission relationship sync requires policy bindings to refresh
  successfully in the same run.

## References

- [Google Cloud resource hierarchy](https://cloud.google.com/resource-manager/docs/cloud-platform-resource-hierarchy#organizations)
- [Application Default Credentials](https://cloud.google.com/docs/authentication/production)
- [Cloud Asset Inventory](https://cloud.google.com/asset-inventory/docs/overview)
