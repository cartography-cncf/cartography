from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class GitHubDependencyNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Canonical dependency name, optionally combined with its requirement string.",
    )
    name: PropertyRef = PropertyRef(
        "name", description="Ecosystem-normalized dependency name."
    )
    original_name: PropertyRef = PropertyRef(
        "original_name",
        description="Package name as reported by the GitHub dependency graph.",
    )
    requirements: PropertyRef = PropertyRef(
        "requirements", description="Original dependency requirement string."
    )
    ecosystem: PropertyRef = PropertyRef(
        "ecosystem", description="Normalized package ecosystem."
    )
    package_manager: PropertyRef = PropertyRef(
        "package_manager",
        description="Package manager reported by the GitHub dependency graph.",
    )
    manifest_file: PropertyRef = PropertyRef(
        "manifest_file",
        description="Name of the manifest that declares the dependency.",
    )
    version: PropertyRef = PropertyRef(
        "version", description="Exact package version when one can be resolved."
    )
    type: PropertyRef = PropertyRef(
        "type", description="Package URL type when an exact version is known."
    )
    purl: PropertyRef = PropertyRef(
        "purl", description="Package URL returned by GitHub when available."
    )
    normalized_id: PropertyRef = PropertyRef(
        "normalized_id",
        extra_index=True,
        description="Normalized package identifier used for ontology matching.",
    )
    source: PropertyRef = PropertyRef(
        "source",
        description=(
            "Version source: `dependency_graph` for GitHub data or `lockfile` "
            "for lockfile fallback."
        ),
    )
    version_confidence: PropertyRef = PropertyRef(
        "version_confidence",
        description="Derived version certainty: `exact`, `range`, or `unknown`.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitHubDependencyToRepositoryRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    requirements: PropertyRef = PropertyRef(
        "requirements", description="Original dependency requirement string."
    )
    manifest_path: PropertyRef = PropertyRef(
        "manifest_path", description="Path to the dependency manifest."
    )


@dataclass(frozen=True)
class GitHubDependencyToRepositoryRel(CartographyRelSchema):
    """Links a GitHub repository to a software dependency it requires."""

    target_node_label: str = "GitHubRepository"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("repo_url")}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "REQUIRES"
    properties: GitHubDependencyToRepositoryRelProperties = (
        GitHubDependencyToRepositoryRelProperties()
    )


@dataclass(frozen=True)
class DependencyGraphManifestToDependencyRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DependencyGraphManifestToDependencyRel(CartographyRelSchema):
    """Links a dependency manifest to a dependency it declares."""

    target_node_label: str = "GitHubDependencyGraphManifest"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("manifest_id")}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_DEP"
    properties: DependencyGraphManifestToDependencyRelProperties = (
        DependencyGraphManifestToDependencyRelProperties()
    )


@dataclass(frozen=True)
class GitHubDependencySchema(CartographyNodeSchema):
    """
    Dependency is a globally shared package node: the same canonical
    `name|requirements` is referenced by many repositories across many orgs, so
    we cannot scope its node-level cleanup to a single tenant without risking
    cross-tenant deletes (see PythonLibrary for the same pattern). Cleanup is
    therefore unscoped and runs once per sync cycle from
    `cleanup_global_resources`. The links to repositories (REQUIRES) and to
    manifests (HAS_DEP) are modeled as `other_relationships`.
    """

    label: str = "Dependency"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["GitHubDependency"])
    properties: GitHubDependencyNodeProperties = GitHubDependencyNodeProperties()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            GitHubDependencyToRepositoryRel(),
            DependencyGraphManifestToDependencyRel(),
        ]
    )

    @property
    def scoped_cleanup(self) -> bool:
        return False
