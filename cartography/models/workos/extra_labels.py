from dataclasses import dataclass

from cartography.models.core.nodes import ExtraNodeLabel


@dataclass(frozen=True)
class EnvironmentLabel(ExtraNodeLabel):
    """A workos node participating in the shared Environment graph interface."""

    label: str = "Environment"
