from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class CloudflareDNSRecordNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="DNS record ID.")
    name: PropertyRef = PropertyRef(
        "name",
        extra_index=True,
        description="DNS record name.",
    )
    value: PropertyRef = PropertyRef(
        "content",
        description="Value or address to which the record points.",
    )
    type: PropertyRef = PropertyRef("type", description="DNS record type.")
    comment: PropertyRef = PropertyRef("comment", description="DNS record comment.")
    proxied: PropertyRef = PropertyRef(
        "proxied",
        description="Whether Cloudflare proxies the record.",
    )
    ttl: PropertyRef = PropertyRef(
        "ttl",
        description="DNS record TTL; 1 indicates automatic TTL.",
    )
    created_on: PropertyRef = PropertyRef(
        "created_on",
        description="Timestamp when the record was created.",
    )
    modified_on: PropertyRef = PropertyRef(
        "modified_on",
        description="Timestamp when the record was last modified.",
    )
    proxiable: PropertyRef = PropertyRef(
        "proxiable",
        description="Whether Cloudflare can proxy the record.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last update.",
    )


@dataclass(frozen=True)
class CloudflareDNSRecordToZoneRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:CloudflareDNSRecord)<-[:RESOURCE]-(:CloudflareZone)
class CloudflareDNSRecordToZoneRel(CartographyRelSchema):
    """The DNS zone contains the DNS record."""

    target_node_label: str = "CloudflareZone"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("zone_id", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: CloudflareDNSRecordToZoneRelProperties = (
        CloudflareDNSRecordToZoneRelProperties()
    )


@dataclass(frozen=True)
class CloudflareDNSRecordSchema(CartographyNodeSchema):
    """A DNS record in Cloudflare."""

    label: str = "CloudflareDNSRecord"
    properties: CloudflareDNSRecordNodeProperties = CloudflareDNSRecordNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["DNSRecord"])
    sub_resource_relationship: CloudflareDNSRecordToZoneRel = (
        CloudflareDNSRecordToZoneRel()
    )
