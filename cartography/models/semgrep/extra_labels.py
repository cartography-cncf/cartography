from cartography.models.core.nodes import ExtraNodeLabel
from cartography.models.core.nodes import LabelKind

SEMGREP_DEPENDENCY = ExtraNodeLabel(
    label="SemgrepDependency",
    description="A semgrep node participating in the shared SemgrepDependency graph interface.",
)


LEGACY_GO_LIBRARY = ExtraNodeLabel(
    label="GoLibrary",
    description="Compatibility label for the deprecated `GoLibrary` semgrep node label.",
    kind=LabelKind.COMPATIBILITY,
    replacement_label="SemgrepGoLibrary",
    remove_in="1.0.0",
)


LEGACY_NPM_LIBRARY = ExtraNodeLabel(
    label="NpmLibrary",
    description="Compatibility label for the deprecated `NpmLibrary` semgrep node label.",
    kind=LabelKind.COMPATIBILITY,
    replacement_label="SemgrepNpmLibrary",
    remove_in="1.0.0",
)
