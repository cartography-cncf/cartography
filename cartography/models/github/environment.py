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
from cartography.models.core.relationships import OtherRelationships
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
    """Relationship from environment to its repository."""

    target_node_label: str = "GitHubRepository"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("repo_url")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_ENVIRONMENT"
    properties: GitHubEnvironmentToRepoRelProperties = (
        GitHubEnvironmentToRepoRelProperties()
    )


@dataclass(frozen=True)
class GitHubEnvironmentToOrgRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitHubEnvironmentToOrgRel(CartographyRelSchema):
    """
    Sub-resource relationship from environment to organization.

    This uses org as the sub-resource so that cleanup is scoped to the organization.
    """

    target_node_label: str = "GitHubOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("org_url", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GitHubEnvironmentToOrgRelProperties = (
        GitHubEnvironmentToOrgRelProperties()
    )


@dataclass(frozen=True)
class GitHubEnvironmentSchema(CartographyNodeSchema):
    """
    Schema for GitHub deployment environments.

    Uses GitHubOrganization as the sub-resource for cleanup scoping.
    The relationship to GitHubRepository is in other_relationships.
    """

    label: str = "GitHubEnvironment"
    properties: GitHubEnvironmentNodeProperties = GitHubEnvironmentNodeProperties()
    sub_resource_relationship: GitHubEnvironmentToOrgRel = GitHubEnvironmentToOrgRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [GitHubEnvironmentToRepoRel()],
    )
