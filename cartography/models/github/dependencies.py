from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class GitHubDependencyNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name", extra_index=True)
    original_name: PropertyRef = PropertyRef("original_name")
    version: PropertyRef = PropertyRef("version")
    ecosystem: PropertyRef = PropertyRef("ecosystem", extra_index=True)
    package_manager: PropertyRef = PropertyRef("package_manager")
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
    properties: GitHubDependencyToRepositoryRelProperties = GitHubDependencyToRepositoryRelProperties()


@dataclass(frozen=True)
class GitHubDependencySchema(CartographyNodeSchema):
    label: str = "Dependency"
    properties: GitHubDependencyNodeProperties = GitHubDependencyNodeProperties()
    sub_resource_relationship: GitHubDependencyToRepositoryRel = GitHubDependencyToRepositoryRel() 