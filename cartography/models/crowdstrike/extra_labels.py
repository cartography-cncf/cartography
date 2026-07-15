from dataclasses import dataclass

from cartography.models.core.nodes import ExtraNodeLabel


@dataclass(frozen=True)
class LegacySpotlightVulnerabilityLabel(ExtraNodeLabel):
    """Compatibility label for the deprecated `SpotlightVulnerability` crowdstrike node label."""

    label: str = "SpotlightVulnerability"
