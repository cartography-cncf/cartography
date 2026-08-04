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
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class GitHubActionsVariableNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Scope-qualified GitHub Actions variable identifier."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Variable name."
    )
    value: PropertyRef = PropertyRef(
        "value", description="Plaintext variable value returned by GitHub."
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="Timestamp when the variable was created."
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at", description="Timestamp when the variable was last updated."
    )
    visibility: PropertyRef = PropertyRef(
        "visibility",
        description="Organization variable visibility: `all`, `private`, or `selected`.",
    )
    level: PropertyRef = PropertyRef(
        "level",
        description="Variable scope: `organization`, `repository`, or `environment`.",
    )


# =============================================================================
# Organization Level
# =============================================================================


@dataclass(frozen=True)
class GitHubActionsVariableToOrgRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitHubActionsVariableToOrgRel(CartographyRelSchema):
    """Scopes a GitHub resource to its organization."""

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
    """A plaintext GitHub Actions variable at organization, repository, or environment scope."""

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
    """Links a GitHub repository to an Actions variable."""

    target_node_label: str = "GitHubRepository"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("repo_url")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_VARIABLE"
    properties: GitHubActionsVariableToRepoRelProperties = (
        GitHubActionsVariableToRepoRelProperties()
    )


@dataclass(frozen=True)
class GitHubRepoActionsVariableSchema(CartographyNodeSchema):
    """A plaintext GitHub Actions variable at organization, repository, or environment scope."""

    label: str = "GitHubActionsVariable"
    properties: GitHubActionsVariableNodeProperties = (
        GitHubActionsVariableNodeProperties()
    )
    sub_resource_relationship: GitHubActionsVariableToOrgRel = (
        GitHubActionsVariableToOrgRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [GitHubActionsVariableToRepoRel()]
    )


# =============================================================================
# Environment Level
# =============================================================================


@dataclass(frozen=True)
class GitHubActionsVariableToEnvRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitHubActionsVariableToEnvRel(CartographyRelSchema):
    """Relationship from environment-level variable to its environment."""

    target_node_label: str = "GitHubEnvironment"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("env_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_VARIABLE"
    properties: GitHubActionsVariableToEnvRelProperties = (
        GitHubActionsVariableToEnvRelProperties()
    )


@dataclass(frozen=True)
class GitHubEnvActionsVariableToOrgRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitHubEnvActionsVariableToOrgRel(CartographyRelSchema):
    """Scopes a GitHub resource to its organization."""

    target_node_label: str = "GitHubOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("org_url", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GitHubEnvActionsVariableToOrgRelProperties = (
        GitHubEnvActionsVariableToOrgRelProperties()
    )


@dataclass(frozen=True)
class GitHubEnvActionsVariableSchema(CartographyNodeSchema):
    """A plaintext GitHub Actions variable at organization, repository, or environment scope."""

    label: str = "GitHubActionsVariable"
    properties: GitHubActionsVariableNodeProperties = (
        GitHubActionsVariableNodeProperties()
    )
    sub_resource_relationship: GitHubEnvActionsVariableToOrgRel = (
        GitHubEnvActionsVariableToOrgRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [GitHubActionsVariableToEnvRel()],
    )
