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
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class GitHubActionsSecretNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Scope-qualified GitHub Actions secret identifier."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Secret name."
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="Timestamp when the secret metadata was created."
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at", description="Timestamp when the secret metadata was last updated."
    )
    visibility: PropertyRef = PropertyRef(
        "visibility",
        description="Organization secret visibility: `all`, `private`, or `selected`.",
    )
    level: PropertyRef = PropertyRef(
        "level",
        description="Secret scope: `organization`, `repository`, or `environment`.",
    )


# =============================================================================
# Organization Level
# =============================================================================


@dataclass(frozen=True)
class GitHubActionsSecretToOrgRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitHubActionsSecretToOrgRel(CartographyRelSchema):
    """Scopes a GitHub resource to its organization."""

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
    """A GitHub Actions secret at organization, repository, or environment scope.

    GitHub exposes metadata but never the secret value.
    """

    label: str = "GitHubActionsSecret"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        ["Secret"]
    )  # Secret label is used for ontology mapping
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
    """Links a GitHub repository to an Actions secret."""

    target_node_label: str = "GitHubRepository"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("repo_url")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_SECRET"
    properties: GitHubActionsSecretToRepoRelProperties = (
        GitHubActionsSecretToRepoRelProperties()
    )


@dataclass(frozen=True)
class GitHubRepoActionsSecretSchema(CartographyNodeSchema):
    """A GitHub Actions secret at organization, repository, or environment scope.

    GitHub exposes metadata but never the secret value.
    """

    label: str = "GitHubActionsSecret"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        ["Secret"]
    )  # Secret label is used for ontology mapping
    properties: GitHubActionsSecretNodeProperties = GitHubActionsSecretNodeProperties()
    sub_resource_relationship: GitHubActionsSecretToOrgRel = (
        GitHubActionsSecretToOrgRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [GitHubActionsSecretToRepoRel()]
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
    """Scopes a GitHub resource to its organization."""

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
    """A GitHub Actions secret at organization, repository, or environment scope.

    GitHub exposes metadata but never the secret value.
    """

    label: str = "GitHubActionsSecret"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        ["Secret"]
    )  # Secret label is used for ontology mapping
    properties: GitHubActionsSecretNodeProperties = GitHubActionsSecretNodeProperties()
    sub_resource_relationship: GitHubEnvActionsSecretToOrgRel = (
        GitHubEnvActionsSecretToOrgRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [GitHubActionsSecretToEnvRel()],
    )
