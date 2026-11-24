from cartography.models.core.nodes import ExtraNodeLabel
from cartography.models.core.nodes import LabelKind

INSTANCE = ExtraNodeLabel(
    label="Instance",
    description="A gcp node participating in the shared Instance graph interface.",
)


LABEL = ExtraNodeLabel(
    label="Label",
    description="A gcp node participating in the shared Label graph interface.",
)


LEGACY_GCP_BUCKET_LABEL = ExtraNodeLabel(
    label="GCPBucketLabel",
    description="Compatibility label for the deprecated `GCPBucketLabel` gcp node label.",
    kind=LabelKind.COMPATIBILITY,
    replacement_label="GCPLabel",
    remove_in="1.0.0",
)
