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
    # Layer, build provenance and parent image enrichment for Artifact Registry
    # images. Separate from artifact_registry because on registries with
    # millions of images it costs far more than the inventory itself.
    "artifact_registry_image_layers",
    "cloud_run",
    "bigquery",
    "bigquery_connection",
    "apikeys",
    "policy_bindings",
    "permission_relationships",
]
