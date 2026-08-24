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
    id: PropertyRef = PropertyRef("id", description="The Netlify DNS zone id.")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", extra_index=True, description="Zone name.")
    domain: PropertyRef = PropertyRef(
        "domain",
        description="Apex domain of the zone. Taken from the domain registration's name when the domain was bought through Netlify.",
    )
    # Set only for a domain bought through Netlify, where the API returns the whole domain
    # registration on `domain` and transform() flattens the renewal fields onto the zone. A
    # domain near expiry, with auto-renew off, or with a failed payment is a hijack candidate.
    domain_registered_at: PropertyRef = PropertyRef(
        "domain_registered_at",
        description="When the apex domain was registered, for a domain bought through Netlify.",
    )
    domain_expires_at: PropertyRef = PropertyRef(
        "domain_expires_at",
        description="When the domain registration expires. A near expiry is a hijack candidate.",
    )
    domain_auto_renew: PropertyRef = PropertyRef(
        "domain_auto_renew",
        description="Whether the registration renews automatically. A false value is a hijack candidate.",
    )
    domain_registration_status: PropertyRef = PropertyRef(
        "domain_registration_status",
        description="Registration status Netlify reports, e.g. `payment_succeeded`.",
    )
    # Set when the zone is attached to a specific site rather than held at team level.
    site_id: PropertyRef = PropertyRef(
        "site_id",
        description="Id of the site the zone is attached to, when it is not held at team level.",
    )
    dns_servers: PropertyRef = PropertyRef(
        "dns_servers", description="Nameservers the zone must be delegated to."
    )
    supported_record_types: PropertyRef = PropertyRef(
        "supported_record_types", description="Record types the zone accepts."
    )
    ipv6_enabled: PropertyRef = PropertyRef(
        "ipv6_enabled", description="Whether IPv6 records are enabled."
    )
    dedicated: PropertyRef = PropertyRef(
        "dedicated", description="Whether the zone is on dedicated nameservers."
    )
    # Delegation or validation problems Netlify reports on the zone. A zone in error is a
    # dangling-delegation candidate.
    errors: PropertyRef = PropertyRef(
        "errors",
        description="Delegation or validation problems Netlify reports. A zone in error is a dangling-delegation candidate.",
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="When the zone was created."
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at", description="When the zone was last modified."
    )


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
