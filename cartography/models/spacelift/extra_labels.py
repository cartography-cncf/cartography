from dataclasses import dataclass

from cartography.models.core.nodes import ExtraNodeLabel


@dataclass(frozen=True)
class LegacyCloudTrailSpaceliftEventLabel(ExtraNodeLabel):
    """Compatibility label for the deprecated `CloudTrailSpaceliftEvent` spacelift node label."""

    label: str = "CloudTrailSpaceliftEvent"
