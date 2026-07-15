from dataclasses import dataclass

from cartography.models.core.nodes import ExtraNodeLabel


@dataclass(frozen=True)
class SlackUserLabel(ExtraNodeLabel):
    """A slack node participating in the shared SlackUser graph interface."""

    label: str = "SlackUser"
