from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ConditionalNodeLabel
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class GitHubPersonalAccessTokenNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Stable identifier derived from the organization and access grant.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    token_kind: PropertyRef = PropertyRef(
        "token_kind",
        extra_index=True,
        description="Token kind: `fine_grained` or `classic`.",
    )
    token_id: PropertyRef = PropertyRef(
        "token_id",
        extra_index=True,
        description="Fine-grained PAT token ID, when GitHub returns one.",
    )
    token_name: PropertyRef = PropertyRef(
        "token_name",
        extra_index=True,
        description="Fine-grained PAT name, when available.",
    )
    owner_login: PropertyRef = PropertyRef(
        "owner_login",
        extra_index=True,
        description="Login of the GitHub user who owns the token.",
    )
    repository_selection: PropertyRef = PropertyRef(
        "repository_selection",
        description="Fine-grained PAT repository selection, such as `all` or `selected`.",
    )
    permissions: PropertyRef = PropertyRef(
        "permissions",
        description="Fine-grained PAT permission details encoded as JSON.",
    )
    scopes: PropertyRef = PropertyRef(
        "scopes",
        description="OAuth scopes exposed for a classic PAT SAML authorization.",
    )
    access_granted_at: PropertyRef = PropertyRef(
        "access_granted_at",
        description="Timestamp when fine-grained PAT access to the organization was granted.",
    )
    credential_authorized_at: PropertyRef = PropertyRef(
        "credential_authorized_at",
        description="Timestamp when a classic PAT was authorized for organization SAML SSO.",
    )
    credential_accessed_at: PropertyRef = PropertyRef(
        "credential_accessed_at",
        description="Timestamp of the latest classic PAT SAML authorization access event.",
    )
    expires_at: PropertyRef = PropertyRef(
        "expires_at",
        description="Token or credential authorization expiration timestamp.",
    )
    last_used_at: PropertyRef = PropertyRef(
        "last_used_at",
        description="Timestamp when a fine-grained PAT last called the GitHub API.",
    )


@dataclass(frozen=True)
class GitHubPersonalAccessTokenRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitHubPersonalAccessTokenToOrgRel(CartographyRelSchema):
    """Scopes a GitHub resource to its organization."""

    target_node_label: str = "GitHubOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("org_url", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GitHubPersonalAccessTokenRelProperties = (
        GitHubPersonalAccessTokenRelProperties()
    )


@dataclass(frozen=True)
# DEPRECATED: replaced by the canonical (:APIKey)-[:OWNED_BY]->(:UserAccount)
# edge (GitHubPersonalAccessTokenToOwnerUserOwnedByRel). Kept for backward
# compatibility, will be removed in v1.0.0.
# (:GitHubUser)-[:OWNS]->(:GitHubPersonalAccessToken)
class GitHubPersonalAccessTokenToOwnerUserRel(CartographyRelSchema):
    """Deprecated compatibility edge from a GitHub user to a personal access token."""

    target_node_label: str = "GitHubUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("owner_user_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "OWNS"
    properties: GitHubPersonalAccessTokenRelProperties = (
        GitHubPersonalAccessTokenRelProperties()
    )


@dataclass(frozen=True)
# Canonical ontology edge: (:APIKey)-[:OWNED_BY]->(:UserAccount)
class GitHubPersonalAccessTokenToOwnerUserOwnedByRel(CartographyRelSchema):
    """Links a GitHub personal access token to its owning user."""

    target_node_label: str = "GitHubUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("owner_user_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "OWNED_BY"
    properties: GitHubPersonalAccessTokenRelProperties = (
        GitHubPersonalAccessTokenRelProperties()
    )


@dataclass(frozen=True)
class GitHubPersonalAccessTokenToRepositoryRel(CartographyRelSchema):
    """Links a personal access token to a repository it can access."""

    target_node_label: str = "GitHubRepository"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("repository_urls", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "CAN_ACCESS"
    properties: GitHubPersonalAccessTokenRelProperties = (
        GitHubPersonalAccessTokenRelProperties()
    )


@dataclass(frozen=True)
class GitHubPersonalAccessTokenSchema(CartographyNodeSchema):
    """Metadata for a fine-grained or classic GitHub personal access token visible to an organization administrator."""

    label: str = "GitHubPersonalAccessToken"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        [
            "APIKey",
            ConditionalNodeLabel(
                label="GitHubFineGrainedPersonalAccessToken",
                conditions={"token_kind": "fine_grained"},
            ),
            ConditionalNodeLabel(
                label="GitHubClassicPersonalAccessToken",
                conditions={"token_kind": "classic"},
            ),
        ]
    )
    properties: GitHubPersonalAccessTokenNodeProperties = (
        GitHubPersonalAccessTokenNodeProperties()
    )
    sub_resource_relationship: GitHubPersonalAccessTokenToOrgRel = (
        GitHubPersonalAccessTokenToOrgRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            GitHubPersonalAccessTokenToOwnerUserRel(),
            GitHubPersonalAccessTokenToOwnerUserOwnedByRel(),
            GitHubPersonalAccessTokenToRepositoryRel(),
        ],
    )
