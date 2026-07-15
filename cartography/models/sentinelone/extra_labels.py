from dataclasses import dataclass

from cartography.models.core.nodes import ExtraNodeLabel


@dataclass(frozen=True)
class S1FindingLabel(ExtraNodeLabel):
    """A sentinelone node participating in the shared S1Finding graph interface."""

    label: str = "S1Finding"
