"""
GitHub Environment schema definition.

Represents GitHub deployment environments for repositories.
"""

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
class GitHubEnvironmentNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    html_url: PropertyRef = PropertyRef("html_url")
    created_at: PropertyRef = PropertyRef("created_at")
    updated_at: PropertyRef = PropertyRef("updated_at")


@dataclass(frozen=True)
class GitHubEnvironmentToRepoRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitHubEnvironmentToRepoRel(CartographyRelSchema):
    target_node_label: str = "GitHubRepository"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("repo_url", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_ENVIRONMENT"
    properties: GitHubEnvironmentToRepoRelProperties = (
        GitHubEnvironmentToRepoRelProperties()
    )


@dataclass(frozen=True)
class GitHubEnvironmentSchema(CartographyNodeSchema):
    label: str = "GitHubEnvironment"
    properties: GitHubEnvironmentNodeProperties = GitHubEnvironmentNodeProperties()
    sub_resource_relationship: GitHubEnvironmentToRepoRel = GitHubEnvironmentToRepoRel()
