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
from cartography.models.ontology.labels import DNS_ZONE


# --- Node Definitions ---
@dataclass(frozen=True)
class NetlifyDNSZoneNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    domain: PropertyRef = PropertyRef("domain")
    # Set when the zone is attached to a specific site rather than held at team level.
    site_id: PropertyRef = PropertyRef("site_id")
    dns_servers: PropertyRef = PropertyRef("dns_servers")
    supported_record_types: PropertyRef = PropertyRef("supported_record_types")
    ipv6_enabled: PropertyRef = PropertyRef("ipv6_enabled")
    dedicated: PropertyRef = PropertyRef("dedicated")
    # Delegation or validation problems Netlify reports on the zone. A zone in error is a
    # dangling-delegation candidate.
    errors: PropertyRef = PropertyRef("errors")
    created_at: PropertyRef = PropertyRef("created_at")
    updated_at: PropertyRef = PropertyRef("updated_at")


# --- Relationship Definitions ---
@dataclass(frozen=True)
class NetlifyDNSZoneToNetlifyAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:NetlifyAccount)-[:RESOURCE]->(:NetlifyDNSZone)
class NetlifyDNSZoneToNetlifyAccountRel(CartographyRelSchema):
    target_node_label: str = "NetlifyAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("NETLIFY_ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: NetlifyDNSZoneToNetlifyAccountRelProperties = (
        NetlifyDNSZoneToNetlifyAccountRelProperties()
    )


@dataclass(frozen=True)
class NetlifyDNSZoneToSiteRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:NetlifySite)-[:HAS_DNS_ZONE]->(:NetlifyDNSZone)
class NetlifyDNSZoneToSiteRel(CartographyRelSchema):
    target_node_label: str = "NetlifySite"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("site_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_DNS_ZONE"
    properties: NetlifyDNSZoneToSiteRelProperties = NetlifyDNSZoneToSiteRelProperties()


# --- Main Schema ---
@dataclass(frozen=True)
class NetlifyDNSZoneSchema(CartographyNodeSchema):
    """
    A DNS zone hosted on Netlify DNS.
    """

    label: str = "NetlifyDNSZone"
    properties: NetlifyDNSZoneNodeProperties = NetlifyDNSZoneNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([DNS_ZONE])
    sub_resource_relationship: NetlifyDNSZoneToNetlifyAccountRel = (
        NetlifyDNSZoneToNetlifyAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [NetlifyDNSZoneToSiteRel()],
    )
