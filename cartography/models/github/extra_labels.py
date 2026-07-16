from cartography.models.core.nodes import ExtraNodeLabel
from cartography.models.core.nodes import LabelKind

GIT_HUB_CLASSIC_PERSONAL_ACCESS_TOKEN = ExtraNodeLabel(
    label="GitHubClassicPersonalAccessToken",
    description="A github node participating in the shared GitHubClassicPersonalAccessToken graph interface.",
)


GIT_HUB_DEPENDENCY = ExtraNodeLabel(
    label="GitHubDependency",
    description="A github node participating in the shared GitHubDependency graph interface.",
)


GIT_HUB_FINE_GRAINED_PERSONAL_ACCESS_TOKEN = ExtraNodeLabel(
    label="GitHubFineGrainedPersonalAccessToken",
    description="A github node participating in the shared GitHubFineGrainedPersonalAccessToken graph interface.",
)


LEGACY_DEPENDENCY_GRAPH_MANIFEST = ExtraNodeLabel(
    label="DependencyGraphManifest",
    description="Compatibility label for the deprecated `DependencyGraphManifest` github node label.",
    kind=LabelKind.COMPATIBILITY,
    remove_in="v1.0.0",
)
