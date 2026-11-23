from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_source_node_matcher
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import SourceNodeMatcher
from cartography.models.core.relationships import TargetNodeMatcher
from cartography.models.github.extra_labels import GIT_HUB_CLASSIC_PERSONAL_ACCESS_TOKEN
from cartography.models.github.extra_labels import (
    GIT_HUB_FINE_GRAINED_PERSONAL_ACCESS_TOKEN,
)
from cartography.models.ontology.labels import API_KEY


@dataclass(frozen=True)
class GitHubPersonalAccessTokenNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description=(
            "Stable identifier. Fine-grained PATs are keyed by the organization's "
            "access grant, since a fine-grained PAT has a single resource owner. "
            "Classic PATs are keyed by GitHub's `authorized_credential_id`, the "
            "token's own ID, so one token authorized for several organizations is one "
            "node. When GitHub omits it, the ID falls back to the organization's "
            "`credential-authorizations/{credential_id}`."
        ),
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
        description=(
            "Timestamp when a classic PAT was authorized for SAML SSO, as reported by "
            "the most recently synced organization. Each organization's own value is "
            "on its `AUTHORIZED_CREDENTIAL` edge."
        ),
    )
    credential_accessed_at: PropertyRef = PropertyRef(
        "credential_accessed_at",
        description=(
            "Timestamp of the latest classic PAT SAML authorization access event, as "
            "reported by the most recently synced organization. Each organization's "
            "own value is on its `AUTHORIZED_CREDENTIAL` edge."
        ),
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
    """Scopes a fine-grained GitHub personal access token to the organization it was granted access to."""

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
    """A fine-grained GitHub personal access token granted access to an organization. Classic tokens use GitHubClassicPersonalAccessTokenSchema."""

    label: str = "GitHubPersonalAccessToken"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        [
            API_KEY,
            GIT_HUB_FINE_GRAINED_PERSONAL_ACCESS_TOKEN.when(token_kind="fine_grained"),
            GIT_HUB_CLASSIC_PERSONAL_ACCESS_TOKEN.when(token_kind="classic"),
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


@dataclass(frozen=True)
class GitHubClassicPersonalAccessTokenSchema(CartographyNodeSchema):
    """
    A classic GitHub personal access token authorized for SAML SSO in one or more organizations.

    The node carries no sub-resource relationship: one token can be authorized in
    several organizations that are synced separately, and an organization-scoped
    cleanup would delete a token another organization still authorizes. Each
    organization's authorization is an `AUTHORIZED_CREDENTIAL` MatchLink cleaned up
    per organization, and the node is deleted once no authorization remains.
    """

    label: str = "GitHubPersonalAccessToken"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        [API_KEY, GIT_HUB_CLASSIC_PERSONAL_ACCESS_TOKEN]
    )
    properties: GitHubPersonalAccessTokenNodeProperties = (
        GitHubPersonalAccessTokenNodeProperties()
    )
    sub_resource_relationship: None = None
    other_relationships: OtherRelationships = OtherRelationships(
        [
            GitHubPersonalAccessTokenToOwnerUserRel(),
            GitHubPersonalAccessTokenToOwnerUserOwnedByRel(),
        ],
    )


@dataclass(frozen=True)
class GitHubCredentialAuthorizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label", set_in_kwargs=True
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)
    credential_id: PropertyRef = PropertyRef(
        "credential_id",
        description=(
            "ID of this organization's SAML SSO authorization of the token. Revoke "
            "the token's access to the organization with "
            "`DELETE /orgs/{org}/credential-authorizations/{credential_id}`."
        ),
    )
    credential_authorized_at: PropertyRef = PropertyRef(
        "credential_authorized_at",
        description="Timestamp when the token was authorized for this organization.",
    )
    credential_accessed_at: PropertyRef = PropertyRef(
        "credential_accessed_at",
        description="Timestamp of the latest access event for this authorization.",
    )


@dataclass(frozen=True)
# (:GitHubOrganization)-[:AUTHORIZED_CREDENTIAL]->(:GitHubPersonalAccessToken)
class GitHubOrganizationAuthorizedCredentialMatchLink(CartographyRelSchema):
    """An organization's SAML SSO authorization of a classic personal access token."""

    source_node_label: str = "GitHubOrganization"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("org_url")},
    )
    target_node_label: str = "GitHubPersonalAccessToken"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "AUTHORIZED_CREDENTIAL"
    properties: GitHubCredentialAuthorizationRelProperties = (
        GitHubCredentialAuthorizationRelProperties()
    )
