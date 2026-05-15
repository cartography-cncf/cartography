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
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    token_kind: PropertyRef = PropertyRef("token_kind", extra_index=True)
    token_id: PropertyRef = PropertyRef("token_id", extra_index=True)
    token_name: PropertyRef = PropertyRef("token_name", extra_index=True)
    owner_login: PropertyRef = PropertyRef("owner_login", extra_index=True)
    repository_selection: PropertyRef = PropertyRef("repository_selection")
    permissions: PropertyRef = PropertyRef("permissions")
    scopes: PropertyRef = PropertyRef("scopes")
    access_granted_at: PropertyRef = PropertyRef("access_granted_at")
    credential_authorized_at: PropertyRef = PropertyRef("credential_authorized_at")
    credential_accessed_at: PropertyRef = PropertyRef("credential_accessed_at")
    expires_at: PropertyRef = PropertyRef("expires_at")
    last_used_at: PropertyRef = PropertyRef("last_used_at")


@dataclass(frozen=True)
class GitHubPersonalAccessTokenRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitHubPersonalAccessTokenToOrgRel(CartographyRelSchema):
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
class GitHubPersonalAccessTokenToOwnerUserRel(CartographyRelSchema):
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
class GitHubPersonalAccessTokenToRepositoryRel(CartographyRelSchema):
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
            GitHubPersonalAccessTokenToRepositoryRel(),
        ],
    )
