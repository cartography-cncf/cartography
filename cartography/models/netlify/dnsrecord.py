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
from cartography.models.ontology.labels import DNS_RECORD


# --- Node Definitions ---
@dataclass(frozen=True)
class NetlifyDNSRecordNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="The Netlify DNS record id.")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    # Netlify calls the record name `hostname`; it is copied to `name` in transform() so the
    # DNSRecord ontology mapping has the field it requires.
    name: PropertyRef = PropertyRef(
        "name",
        extra_index=True,
        description="Record hostname. Netlify calls this `hostname`; it is copied to `name` for the ontology mapping.",
    )
    hostname: PropertyRef = PropertyRef(
        "hostname", description="Record hostname as Netlify reports it."
    )
    type: PropertyRef = PropertyRef(
        "type", description="Record type, e.g. `A`, `CNAME`, `MX`, `TXT`."
    )
    value: PropertyRef = PropertyRef(
        "value", extra_index=True, description="Record value or target."
    )
    ttl: PropertyRef = PropertyRef("ttl", description="Time to live, in seconds.")
    priority: PropertyRef = PropertyRef(
        "priority", description="Priority, for `MX` and `SRV` records."
    )
    dns_zone_id: PropertyRef = PropertyRef(
        "dns_zone_id", description="Id of the zone holding the record."
    )
    site_id: PropertyRef = PropertyRef(
        "site_id",
        description="Id of the site the record points at, when Netlify manages it.",
    )
    # True when Netlify created and maintains the record itself, for example the records that
    # point a custom domain at the site. A false value means someone set it by hand.
    managed: PropertyRef = PropertyRef(
        "managed",
        description="Whether Netlify created and maintains the record itself. A false value means someone set it by hand.",
    )
    # CAA-specific fields.
    flag: PropertyRef = PropertyRef("flag", description="CAA flag.")
    tag: PropertyRef = PropertyRef("tag", description="CAA tag.")


# --- Relationship Definitions ---
@dataclass(frozen=True)
class NetlifyDNSRecordToNetlifyAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:NetlifyAccount)-[:RESOURCE]->(:NetlifyDNSRecord)
class NetlifyDNSRecordToNetlifyAccountRel(CartographyRelSchema):
    target_node_label: str = "NetlifyAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("NETLIFY_ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: NetlifyDNSRecordToNetlifyAccountRelProperties = (
        NetlifyDNSRecordToNetlifyAccountRelProperties()
    )


@dataclass(frozen=True)
class NetlifyDNSRecordToZoneRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:NetlifyDNSZone)-[:HAS_DNS_RECORD]->(:NetlifyDNSRecord)
class NetlifyDNSRecordToZoneRel(CartographyRelSchema):
    target_node_label: str = "NetlifyDNSZone"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("dns_zone_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_DNS_RECORD"
    properties: NetlifyDNSRecordToZoneRelProperties = (
        NetlifyDNSRecordToZoneRelProperties()
    )


# --- Main Schema ---
@dataclass(frozen=True)
class NetlifyDNSRecordSchema(CartographyNodeSchema):
    """
    A record in a Netlify DNS zone.
    """

    label: str = "NetlifyDNSRecord"
    properties: NetlifyDNSRecordNodeProperties = NetlifyDNSRecordNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([DNS_RECORD])
    sub_resource_relationship: NetlifyDNSRecordToNetlifyAccountRel = (
        NetlifyDNSRecordToNetlifyAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [NetlifyDNSRecordToZoneRel()],
    )
