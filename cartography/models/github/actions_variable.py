"""
GitHub Actions Variable schema definitions.

Variables can exist at three levels:
- Organization-level: variables shared across repos
- Repository-level: variables specific to a repo
- Environment-level: variables specific to a deployment environment

Unlike secrets, variable values are stored in plaintext.
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
class GitHubActionsVariableNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    value: PropertyRef = PropertyRef("value")
    created_at: PropertyRef = PropertyRef("created_at")
    updated_at: PropertyRef = PropertyRef("updated_at")
    visibility: PropertyRef = PropertyRef("visibility")
    level: PropertyRef = PropertyRef("level")


# =============================================================================
# Organization Level
# =============================================================================


@dataclass(frozen=True)
class GitHubActionsVariableToOrgRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitHubActionsVariableToOrgRel(CartographyRelSchema):
    target_node_label: str = "GitHubOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("org_url", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GitHubActionsVariableToOrgRelProperties = (
        GitHubActionsVariableToOrgRelProperties()
    )


@dataclass(frozen=True)
class GitHubOrgActionsVariableSchema(CartographyNodeSchema):
    """Schema for organization-level variables."""

    label: str = "GitHubActionsVariable"
    properties: GitHubActionsVariableNodeProperties = (
        GitHubActionsVariableNodeProperties()
    )
    sub_resource_relationship: GitHubActionsVariableToOrgRel = (
        GitHubActionsVariableToOrgRel()
    )


# =============================================================================
# Repository Level
# =============================================================================


@dataclass(frozen=True)
class GitHubActionsVariableToRepoRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitHubActionsVariableToRepoRel(CartographyRelSchema):
    target_node_label: str = "GitHubRepository"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("repo_url", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_VARIABLE"
    properties: GitHubActionsVariableToRepoRelProperties = (
        GitHubActionsVariableToRepoRelProperties()
    )


@dataclass(frozen=True)
class GitHubRepoActionsVariableSchema(CartographyNodeSchema):
    """Schema for repository-level variables."""

    label: str = "GitHubActionsVariable"
    properties: GitHubActionsVariableNodeProperties = (
        GitHubActionsVariableNodeProperties()
    )
    sub_resource_relationship: GitHubActionsVariableToRepoRel = (
        GitHubActionsVariableToRepoRel()
    )


# =============================================================================
# Environment Level
# =============================================================================


@dataclass(frozen=True)
class GitHubActionsVariableToEnvRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitHubActionsVariableToEnvRel(CartographyRelSchema):
    target_node_label: str = "GitHubEnvironment"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("env_id", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_VARIABLE"
    properties: GitHubActionsVariableToEnvRelProperties = (
        GitHubActionsVariableToEnvRelProperties()
    )


@dataclass(frozen=True)
class GitHubEnvActionsVariableSchema(CartographyNodeSchema):
    """Schema for environment-level variables."""

    label: str = "GitHubActionsVariable"
    properties: GitHubActionsVariableNodeProperties = (
        GitHubActionsVariableNodeProperties()
    )
    sub_resource_relationship: GitHubActionsVariableToEnvRel = (
        GitHubActionsVariableToEnvRel()
    )
