from dataclasses import dataclass

from cartography.models.core.nodes import ExtraNodeLabel


@dataclass(frozen=True)
class GroupLabel(ExtraNodeLabel):
    """A vercel node participating in the shared Group graph interface."""

    label: str = "Group"
