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
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name")
    original_name: PropertyRef = PropertyRef("original_name")
    requirements: PropertyRef = PropertyRef("requirements")
    ecosystem: PropertyRef = PropertyRef("ecosystem")
    package_manager: PropertyRef = PropertyRef("package_manager")
    manifest_file: PropertyRef = PropertyRef("manifest_file")
    version: PropertyRef = PropertyRef("version")
    type: PropertyRef = PropertyRef("type")
    purl: PropertyRef = PropertyRef("purl")
    normalized_id: PropertyRef = PropertyRef("normalized_id", extra_index=True)
    source: PropertyRef = PropertyRef("source")
    version_confidence: PropertyRef = PropertyRef("version_confidence")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitHubDependencyToRepositoryRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    requirements: PropertyRef = PropertyRef("requirements")
    manifest_path: PropertyRef = PropertyRef("manifest_path")


@dataclass(frozen=True)
class GitHubDependencyToRepositoryRel(CartographyRelSchema):
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
    A GitHub dependency is a globally shared package node: the same canonical
    `name|requirements` is referenced by many repositories across many orgs, so
    we cannot scope its node-level cleanup to a single tenant without risking
    cross-tenant deletes (see PythonLibrary for the same pattern). Cleanup is
    therefore unscoped and runs once per sync cycle from
    `cleanup_global_resources`. The links to repositories (REQUIRES) and to
    manifests (HAS_DEP) are modeled as `other_relationships`.

    The primary label is `GitHubDependency` so that this module's unscoped
    cleanup only ever reaps nodes it ingested itself. `Dependency` is the shared
    ontology label carried by every dependency producer (Semgrep, SocketDev,
    ...); it must stay a secondary label here, otherwise github's cleanup would
    delete other modules' `Dependency` nodes (see issue #3035).
    """

    label: str = "GitHubDependency"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Dependency"])
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
