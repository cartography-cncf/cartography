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
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name", extra_index=True)
    value: PropertyRef = PropertyRef("content")
    type: PropertyRef = PropertyRef("type")
    comment: PropertyRef = PropertyRef("comment")
    proxied: PropertyRef = PropertyRef("proxied")
    ttl: PropertyRef = PropertyRef("ttl")
    created_on: PropertyRef = PropertyRef("created_on")
    modified_on: PropertyRef = PropertyRef("modified_on")
    proxiable: PropertyRef = PropertyRef("proxiable")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class CloudflareDNSRecordToZoneRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:CloudflareDNSRecord)<-[:RESOURCE]-(:CloudflareZone)
class CloudflareDNSRecordToZoneRel(CartographyRelSchema):
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
    label: str = "CloudflareDNSRecord"
    properties: CloudflareDNSRecordNodeProperties = CloudflareDNSRecordNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["DNSRecord"])
    sub_resource_relationship: CloudflareDNSRecordToZoneRel = (
        CloudflareDNSRecordToZoneRel()
    )
