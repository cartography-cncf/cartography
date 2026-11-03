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
from cartography.models.ontology.labels import API_KEY


@dataclass(frozen=True)
class OktaApiTokenNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Unique Okta API token identifier.")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this resource.",
    )
    name: PropertyRef = PropertyRef("name", description="Token name.")
    client_name: PropertyRef = PropertyRef(
        "client_name",
        description="Client that created the token, such as `Okta API` for Admin Console tokens.",
    )
    user_id: PropertyRef = PropertyRef(
        "user_id",
        description="ID of the Okta user who owns the token. The token acts with that user's admin roles.",
    )
    token_window: PropertyRef = PropertyRef(
        "token_window",
        description="ISO 8601 duration of inactivity after which the token expires, such as `P30D`.",
    )
    created: PropertyRef = PropertyRef(
        "created", description="Time when the token was created."
    )
    expires_at: PropertyRef = PropertyRef(
        "expires_at",
        description=(
            "Time when the token expires if it is not used again. Okta extends it "
            "by `token_window` each time the token is used, so it is the last use "
            "plus `token_window`; Okta does not expose the last-use time directly."
        ),
    )
    okta_last_updated: PropertyRef = PropertyRef(
        "okta_last_updated", description="Time when Okta last updated the token."
    )
    network_connection: PropertyRef = PropertyRef(
        "network_connection",
        description=(
            "Network condition on token use: `ANYWHERE`, or `ZONE` when the token is "
            "only accepted from (or outside) specific network zones."
        ),
    )


@dataclass(frozen=True)
class OktaApiTokenRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this relationship.",
    )


@dataclass(frozen=True)
class OktaApiTokenToOrganizationRel(CartographyRelSchema):
    """An Okta organization contains an API token."""

    target_node_label: str = "OktaOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("OKTA_ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: OktaApiTokenRelProperties = OktaApiTokenRelProperties()


@dataclass(frozen=True)
class OktaApiTokenOwnedByUserRel(CartographyRelSchema):
    """An Okta API token is owned by, and acts as, an Okta user."""

    target_node_label: str = "OktaUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("user_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "OWNED_BY"
    properties: OktaApiTokenRelProperties = OktaApiTokenRelProperties()


@dataclass(frozen=True)
class OktaApiTokenAllowedFromZoneRel(CartographyRelSchema):
    """An Okta API token can only be used from a network zone."""

    target_node_label: str = "OktaNetworkZone"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("network_include_zone_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ALLOWED_FROM"
    properties: OktaApiTokenRelProperties = OktaApiTokenRelProperties()


@dataclass(frozen=True)
class OktaApiTokenBlockedFromZoneRel(CartographyRelSchema):
    """An Okta API token cannot be used from a network zone."""

    target_node_label: str = "OktaNetworkZone"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("network_exclude_zone_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "BLOCKED_FROM"
    properties: OktaApiTokenRelProperties = OktaApiTokenRelProperties()


@dataclass(frozen=True)
class OktaApiTokenSchema(CartographyNodeSchema):
    """
    An Okta API token (SSWS token). Its secret is never returned by the API.
    Requires the `okta.apiTokens.read` scope.
    """

    label: str = "OktaApiToken"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([API_KEY])
    properties: OktaApiTokenNodeProperties = OktaApiTokenNodeProperties()
    sub_resource_relationship: OktaApiTokenToOrganizationRel = (
        OktaApiTokenToOrganizationRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            OktaApiTokenOwnedByUserRel(),
            OktaApiTokenAllowedFromZoneRel(),
            OktaApiTokenBlockedFromZoneRel(),
        ],
    )
