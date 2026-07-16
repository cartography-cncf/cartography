from cartography.models.core.nodes import ExtraNodeLabel
from cartography.models.core.nodes import LabelKind

LEGACY_CLOUD_TRAIL_SPACELIFT_EVENT = ExtraNodeLabel(
    label="CloudTrailSpaceliftEvent",
    description="Compatibility label for the deprecated `CloudTrailSpaceliftEvent` spacelift node label.",
    kind=LabelKind.COMPATIBILITY,
    remove_in="v1.0.0",
)
