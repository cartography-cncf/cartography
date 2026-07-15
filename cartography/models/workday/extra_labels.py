from dataclasses import dataclass

from cartography.models.core.nodes import ExtraNodeLabel


@dataclass(frozen=True)
class HumanLabel(ExtraNodeLabel):
    """A workday node participating in the shared Human graph interface."""

    label: str = "Human"
