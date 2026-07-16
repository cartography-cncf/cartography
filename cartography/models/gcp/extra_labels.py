from cartography.models.core.nodes import ExtraNodeLabel

GCP_BUCKET_LABEL = ExtraNodeLabel(
    label="GCPBucketLabel",
    description="A gcp node participating in the shared GCPBucketLabel graph interface.",
)


INSTANCE = ExtraNodeLabel(
    label="Instance",
    description="A gcp node participating in the shared Instance graph interface.",
)


LABEL = ExtraNodeLabel(
    label="Label",
    description="A gcp node participating in the shared Label graph interface.",
)
