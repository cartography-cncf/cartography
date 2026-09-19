from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher
from cartography.models.zendesk.tenant import ZendeskRelProperties
from cartography.models.zendesk.tenant import ZendeskResourceToTenantRel


@dataclass(frozen=True)
class ZendeskAPITokenNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Tenant-scoped ID: subdomain:token_id."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    token_id: PropertyRef = PropertyRef(
        "token_id", description="Native legacy API token ID; never the token value."
    )
    creator_user_id: PropertyRef = PropertyRef(
        "creator_user_id",
        description="Creator's user ID, from the API's user_id field with include_users=true; not an authentication identity.",
    )
    assigned_user_id: PropertyRef = PropertyRef(
        "assigned_user_id",
        description="Assigned agent or admin ID, if returned by Zendesk. Distinct from the creator.",
    )
    description: PropertyRef = PropertyRef(
        "description", description="Token description displayed in Admin Center."
    )
    active: PropertyRef = PropertyRef(
        "active",
        description="Whether the token can be used to authenticate API requests.",
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="Token creation time (ISO 8601)."
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at", description="Token modification time (ISO 8601)."
    )
    last_used: PropertyRef = PropertyRef(
        "last_used",
        description="Last authentication time (ISO 8601), or null if never used.",
    )


@dataclass(frozen=True)
class ZendeskAPITokenToCreatorRel(CartographyRelSchema):
    """Links an API token to the staff account that created it, not who can use it."""

    target_node_label: str = "ZendeskUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("creator_node_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CREATED"
    properties: ZendeskRelProperties = ZendeskRelProperties()


@dataclass(frozen=True)
class ZendeskAPITokenSchema(CartographyNodeSchema):
    """Legacy API-token metadata for a Zendesk account; no values or prefixes.

    Source API: `GET /api/v2/api_tokens?include_users=true` (`ListApiTokens`),
    documented in [Zendesk's official OpenAPI specification](https://developer.zendesk.com/zendesk/oas.yaml)
    under `ApiTokenObject` and `ApiTokensResponse`.

    The creator is distinct from the token's authentication authority. See
    [Zendesk's API token documentation](https://support.zendesk.com/hc/en-us/articles/4408889192858-Managing-API-token-access-to-the-Zendesk-API).
    Tokens whose creators are absent from the staff inventory retain their creator
    ID without a CREATED relationship. OAuth tokens are not inventoried.
    Zendesk schedules this endpoint for removal on April 30, 2027.
    """

    label: str = "ZendeskAPIToken"
    properties: ZendeskAPITokenNodeProperties = ZendeskAPITokenNodeProperties()
    sub_resource_relationship: ZendeskResourceToTenantRel = ZendeskResourceToTenantRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [ZendeskAPITokenToCreatorRel()]
    )
