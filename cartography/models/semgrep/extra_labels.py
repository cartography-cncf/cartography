from dataclasses import dataclass

from cartography.models.core.nodes import ExtraNodeLabel


@dataclass(frozen=True)
class SemgrepDependencyLabel(ExtraNodeLabel):
    """A semgrep node participating in the shared SemgrepDependency graph interface."""

    label: str = "SemgrepDependency"
