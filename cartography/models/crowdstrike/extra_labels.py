from cartography.models.core.nodes import ExtraNodeLabel
from cartography.models.core.nodes import LabelKind

LEGACY_SPOTLIGHT_VULNERABILITY = ExtraNodeLabel(
    label="SpotlightVulnerability",
    description="Compatibility label for the deprecated `SpotlightVulnerability` crowdstrike node label.",
    kind=LabelKind.COMPATIBILITY,
    replacement_label="CrowdstrikeSpotlightVulnerability",
    remove_in="1.0.0",
)
