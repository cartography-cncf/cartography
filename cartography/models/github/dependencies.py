from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
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
        {"id": PropertyRef("repo_url", set_in_kwargs=True)}
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
    target_node_label: str = "DependencyGraphManifest"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("manifest_id", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_DEP"
    properties: DependencyGraphManifestToDependencyRelProperties = (
        DependencyGraphManifestToDependencyRelProperties()
    )


@dataclass(frozen=True)
class GitHubDependencySchema(CartographyNodeSchema):
    label: str = "Dependency"
    properties: GitHubDependencyNodeProperties = GitHubDependencyNodeProperties()
    sub_resource_relationship: GitHubDependencyToRepositoryRel = (
        GitHubDependencyToRepositoryRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [DependencyGraphManifestToDependencyRel()]
    )
