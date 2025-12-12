"""
GitHub Actions schema definitions for Workflows, Secrets, Variables, and Environments.

Supports three levels:
- Organization-level: secrets/variables shared across repos
- Repository-level: secrets/variables specific to a repo
- Environment-level: secrets/variables specific to a deployment environment

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
from cartography.models.core.relationships import TargetNodeMatcher

# =============================================================================
# GitHubWorkflow
# =============================================================================


@dataclass(frozen=True)
class GitHubWorkflowNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    path: PropertyRef = PropertyRef("path")
    state: PropertyRef = PropertyRef("state")
    created_at: PropertyRef = PropertyRef("created_at")
    updated_at: PropertyRef = PropertyRef("updated_at")
    html_url: PropertyRef = PropertyRef("html_url")


@dataclass(frozen=True)
class GitHubWorkflowToRepoRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitHubWorkflowToRepoRel(CartographyRelSchema):
    target_node_label: str = "GitHubRepository"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("repo_url", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_WORKFLOW"
    properties: GitHubWorkflowToRepoRelProperties = GitHubWorkflowToRepoRelProperties()


@dataclass(frozen=True)
class GitHubWorkflowSchema(CartographyNodeSchema):
    label: str = "GitHubWorkflow"
    properties: GitHubWorkflowNodeProperties = GitHubWorkflowNodeProperties()
    sub_resource_relationship: GitHubWorkflowToRepoRel = GitHubWorkflowToRepoRel()


# =============================================================================
# GitHubEnvironment
# =============================================================================


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


# =============================================================================
# GitHubActionsSecret - Organization Level
# =============================================================================


@dataclass(frozen=True)
class GitHubActionsSecretNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    created_at: PropertyRef = PropertyRef("created_at")
    updated_at: PropertyRef = PropertyRef("updated_at")
    visibility: PropertyRef = PropertyRef("visibility")
    level: PropertyRef = PropertyRef("level")


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
# GitHubActionsSecret - Repository Level
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
# GitHubActionsSecret - Environment Level
# =============================================================================


@dataclass(frozen=True)
class GitHubActionsSecretToEnvRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitHubActionsSecretToEnvRel(CartographyRelSchema):
    target_node_label: str = "GitHubEnvironment"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("env_id", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_SECRET"
    properties: GitHubActionsSecretToEnvRelProperties = (
        GitHubActionsSecretToEnvRelProperties()
    )


@dataclass(frozen=True)
class GitHubEnvActionsSecretSchema(CartographyNodeSchema):
    """Schema for environment-level secrets."""

    label: str = "GitHubActionsSecret"
    properties: GitHubActionsSecretNodeProperties = GitHubActionsSecretNodeProperties()
    sub_resource_relationship: GitHubActionsSecretToEnvRel = (
        GitHubActionsSecretToEnvRel()
    )


# =============================================================================
# GitHubActionsVariable - Organization Level
# =============================================================================


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
# GitHubActionsVariable - Repository Level
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
# GitHubActionsVariable - Environment Level
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
