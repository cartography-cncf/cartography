"""
GitHub Actions Secret schema definitions.

Secrets can exist at three levels:
- Organization-level: secrets shared across repos
- Repository-level: secrets specific to a repo
- Environment-level: secrets specific to a deployment environment

Note: Secret values are NEVER exposed by the GitHub API - only metadata is stored.
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
class GitHubActionsSecretNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    created_at: PropertyRef = PropertyRef("created_at")
    updated_at: PropertyRef = PropertyRef("updated_at")
    visibility: PropertyRef = PropertyRef("visibility")
    level: PropertyRef = PropertyRef("level")


# =============================================================================
# Organization Level
# =============================================================================


@dataclass(frozen=True)
class GitHubActionsSecretToOrgRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitHubActionsSecretToOrgRel(CartographyRelSchema):
    target_node_label: str = "GitHubOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("org_url", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GitHubActionsSecretToOrgRelProperties = (
        GitHubActionsSecretToOrgRelProperties()
    )


@dataclass(frozen=True)
class GitHubOrgActionsSecretSchema(CartographyNodeSchema):
    """Schema for organization-level secrets."""

    label: str = "GitHubActionsSecret"
    properties: GitHubActionsSecretNodeProperties = GitHubActionsSecretNodeProperties()
    sub_resource_relationship: GitHubActionsSecretToOrgRel = (
        GitHubActionsSecretToOrgRel()
    )


# =============================================================================
# Repository Level
# =============================================================================


@dataclass(frozen=True)
class GitHubActionsSecretToRepoRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitHubActionsSecretToRepoRel(CartographyRelSchema):
    target_node_label: str = "GitHubRepository"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("repo_url", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_SECRET"
    properties: GitHubActionsSecretToRepoRelProperties = (
        GitHubActionsSecretToRepoRelProperties()
    )


@dataclass(frozen=True)
class GitHubRepoActionsSecretSchema(CartographyNodeSchema):
    """Schema for repository-level secrets."""

    label: str = "GitHubActionsSecret"
    properties: GitHubActionsSecretNodeProperties = GitHubActionsSecretNodeProperties()
    sub_resource_relationship: GitHubActionsSecretToRepoRel = (
        GitHubActionsSecretToRepoRel()
    )


# =============================================================================
# Environment Level
# =============================================================================


@dataclass(frozen=True)
class GitHubActionsSecretToEnvRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitHubActionsSecretToEnvRel(CartographyRelSchema):
    """Relationship from environment-level secret to its environment."""

    target_node_label: str = "GitHubEnvironment"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("env_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_SECRET"
    properties: GitHubActionsSecretToEnvRelProperties = (
        GitHubActionsSecretToEnvRelProperties()
    )


@dataclass(frozen=True)
class GitHubEnvActionsSecretToOrgRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitHubEnvActionsSecretToOrgRel(CartographyRelSchema):
    """
    Sub-resource relationship from environment-level secret to organization.

    This uses org as the sub-resource (instead of environment) so that cleanup
    is scoped to the organization. This ensures env-level secrets/variables are
    properly cleaned up even when their parent environment is deleted.
    """

    target_node_label: str = "GitHubOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("org_url", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GitHubEnvActionsSecretToOrgRelProperties = (
        GitHubEnvActionsSecretToOrgRelProperties()
    )


@dataclass(frozen=True)
class GitHubEnvActionsSecretSchema(CartographyNodeSchema):
    """
    Schema for environment-level secrets.

    Uses GitHubOrganization as the sub-resource for cleanup scoping.
    The relationship to GitHubEnvironment is in other_relationships.
    """

    label: str = "GitHubActionsSecret"
    properties: GitHubActionsSecretNodeProperties = GitHubActionsSecretNodeProperties()
    sub_resource_relationship: GitHubEnvActionsSecretToOrgRel = (
        GitHubEnvActionsSecretToOrgRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [GitHubActionsSecretToEnvRel()],
    )
