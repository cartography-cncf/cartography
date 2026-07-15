from dataclasses import dataclass

from cartography.models.core.nodes import ExtraNodeLabel


@dataclass(frozen=True)
class GitLabRepositoryLabel(ExtraNodeLabel):
    """A gitlab node participating in the shared GitLabRepository graph interface."""

    label: str = "GitLabRepository"
