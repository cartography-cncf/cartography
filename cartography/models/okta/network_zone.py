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
class OktaNetworkZoneNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Unique Okta network zone identifier."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this resource.",
    )
    name: PropertyRef = PropertyRef("name", description="Network zone name.")
    type: PropertyRef = PropertyRef(
        "type",
        description=(
            "Zone type: `IP` (gateway and proxy IP addresses), `DYNAMIC` (ASNs, "
            "locations, and proxy type), or `DYNAMIC_V2` (enhanced dynamic zone with "
            "IP service categories such as anonymizers)."
        ),
    )
    status: PropertyRef = PropertyRef(
        "status", description="Zone status, `ACTIVE` or `INACTIVE`."
    )
    usage: PropertyRef = PropertyRef(
        "usage",
        description=(
            "How the zone is used: `POLICY` (referenced by policy and token network "
            "conditions) or `BLOCKLIST` (requests from the zone are denied before "
            "authentication)."
        ),
    )
    system: PropertyRef = PropertyRef(
        "system",
        description=(
            "Whether Okta created the zone, such as `LegacyIpZone`, `BlockedIpZone`, "
            "or `DefaultEnhancedDynamicZone`."
        ),
    )
    created: PropertyRef = PropertyRef(
        "created", description="Time when the zone was created."
    )
    okta_last_updated: PropertyRef = PropertyRef(
        "okta_last_updated", description="Time when Okta last updated the zone."
    )
    gateways: PropertyRef = PropertyRef(
        "gateways",
        description="`IP` zones only. Gateway IP addresses, as CIDRs or `start-end` ranges.",
    )
    proxies: PropertyRef = PropertyRef(
        "proxies",
        description="`IP` zones only. Trusted proxy IP addresses, as CIDRs or `start-end` ranges.",
    )
    use_as_exempt_list: PropertyRef = PropertyRef(
        "use_as_exempt_list",
        description=(
            "`IP` zones only. Whether the zone's IPs are exempt from blocklist zones, "
            "as in the `DefaultExemptIpZone`."
        ),
    )
    asns_include: PropertyRef = PropertyRef(
        "asns_include",
        description="Dynamic zones only. Autonomous system numbers the zone matches.",
    )
    asns_exclude: PropertyRef = PropertyRef(
        "asns_exclude",
        description="`DYNAMIC_V2` zones only. Autonomous system numbers the zone does not match.",
    )
    locations_include: PropertyRef = PropertyRef(
        "locations_include",
        description=(
            "Dynamic zones only. Locations the zone matches, as ISO 3166 country codes "
            "or `country-region` codes."
        ),
    )
    locations_exclude: PropertyRef = PropertyRef(
        "locations_exclude",
        description="`DYNAMIC_V2` zones only. Locations the zone does not match.",
    )
    proxy_type: PropertyRef = PropertyRef(
        "proxy_type",
        description=(
            "`DYNAMIC` zones only. Proxy type the zone matches: `Any`, `TorAnonymizer`, "
            "`NotTorAnonymizer`, or null for none."
        ),
    )
    ip_service_categories_include: PropertyRef = PropertyRef(
        "ip_service_categories_include",
        description=(
            "`DYNAMIC_V2` zones only. IP service categories the zone matches, for "
            "example `ALL_ANONYMIZERS` or `ALL_IP_SERVICES`."
        ),
    )
    ip_service_categories_exclude: PropertyRef = PropertyRef(
        "ip_service_categories_exclude",
        description="`DYNAMIC_V2` zones only. IP service categories the zone does not match.",
    )


@dataclass(frozen=True)
class OktaNetworkZoneToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this relationship.",
    )


@dataclass(frozen=True)
class OktaNetworkZoneToOrganizationRel(CartographyRelSchema):
    """An Okta organization defines a network zone."""

    target_node_label: str = "OktaOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("OKTA_ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: OktaNetworkZoneToOrganizationRelProperties = (
        OktaNetworkZoneToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class OktaNetworkZoneSchema(CartographyNodeSchema):
    """
    An Okta network zone: a set of IP addresses, ASNs, locations, or IP service
    categories that policies and API tokens use to allow or deny requests, or
    that blocks requests outright when used as a blocklist. Requires the
    `okta.networkZones.read` scope.
    """

    label: str = "OktaNetworkZone"
    properties: OktaNetworkZoneNodeProperties = OktaNetworkZoneNodeProperties()
    sub_resource_relationship: OktaNetworkZoneToOrganizationRel = (
        OktaNetworkZoneToOrganizationRel()
    )
