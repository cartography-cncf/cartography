# GCP resource names for selective sync.
# These keys are the valid values for --gcp-requested-syncs.
# Unlike AWS, GCP also checks whether a service is enabled on each project,
# so selective sync is an additional filter on top of service discovery.
RESOURCE_FUNCTIONS: list[str] = [
    "compute",
    "storage",
    "gke",
    "dns",
    "gcf",
    "iam",
    "kms",
    "bigtable",
    "aiplatform",
    "cloud_sql",
    "secretsmanager",
    "artifact_registry",
    "cloud_run",
    "bigquery",
    "bigquery_connection",
    "policy_bindings",
    "permission_relationships",
]
