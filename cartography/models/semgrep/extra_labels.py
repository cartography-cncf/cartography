from dataclasses import dataclass

from cartography.models.core.nodes import ExtraNodeLabel


@dataclass(frozen=True)
class SemgrepDependencyLabel(ExtraNodeLabel):
    """A semgrep node participating in the shared SemgrepDependency graph interface."""

    label: str = "SemgrepDependency"


@dataclass(frozen=True)
class LegacyGoLibraryLabel(ExtraNodeLabel):
    """Compatibility label for the deprecated `GoLibrary` semgrep node label."""

    label: str = "GoLibrary"


@dataclass(frozen=True)
class LegacyNpmLibraryLabel(ExtraNodeLabel):
    """Compatibility label for the deprecated `NpmLibrary` semgrep node label."""

    label: str = "NpmLibrary"
