from dataclasses import dataclass

from cartography.models.core.nodes import ExtraNodeLabel


@dataclass(frozen=True)
class GitHubClassicPersonalAccessTokenLabel(ExtraNodeLabel):
    """A github node participating in the shared GitHubClassicPersonalAccessToken graph interface."""

    label: str = "GitHubClassicPersonalAccessToken"


@dataclass(frozen=True)
class GitHubDependencyLabel(ExtraNodeLabel):
    """A github node participating in the shared GitHubDependency graph interface."""

    label: str = "GitHubDependency"


@dataclass(frozen=True)
class GitHubFineGrainedPersonalAccessTokenLabel(ExtraNodeLabel):
    """A github node participating in the shared GitHubFineGrainedPersonalAccessToken graph interface."""

    label: str = "GitHubFineGrainedPersonalAccessToken"
