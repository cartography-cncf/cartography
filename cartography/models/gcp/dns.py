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


@dataclass(frozen=True)
class GCPDNSZoneNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", extra_index=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    dns_name: PropertyRef = PropertyRef("dns_name")
    description: PropertyRef = PropertyRef("description")
    visibility: PropertyRef = PropertyRef("visibility")
    kind: PropertyRef = PropertyRef("kind")
    nameservers: PropertyRef = PropertyRef("nameservers")
    created_at: PropertyRef = PropertyRef("created_at")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPDNSZoneToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:GCPProject)-[:RESOURCE]->(:GCPDNSZone)
class GCPDNSZoneToProjectRel(CartographyRelSchema):
    target_node_label: str = "GCPProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GCPDNSZoneToProjectRelProperties = GCPDNSZoneToProjectRelProperties()


@dataclass(frozen=True)
class GCPDNSZoneSchema(CartographyNodeSchema):
    label: str = "GCPDNSZone"
    properties: GCPDNSZoneNodeProperties = GCPDNSZoneNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["DNSZone"])
    sub_resource_relationship: GCPDNSZoneToProjectRel = GCPDNSZoneToProjectRel()


@dataclass(frozen=True)
class GCPRecordSetNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", extra_index=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    type: PropertyRef = PropertyRef("type")
    ttl: PropertyRef = PropertyRef("ttl")
    data: PropertyRef = PropertyRef("data")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPRecordSetToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:GCPProject)-[:RESOURCE]->(:GCPRecordSet)
class GCPRecordSetToProjectRel(CartographyRelSchema):
    target_node_label: str = "GCPProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GCPRecordSetToProjectRelProperties = (
        GCPRecordSetToProjectRelProperties()
    )


@dataclass(frozen=True)
class GCPRecordSetToZoneRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:GCPDNSZone)-[:HAS_RECORD]->(:GCPRecordSet)
class GCPRecordSetToZoneRel(CartographyRelSchema):
    target_node_label: str = "GCPDNSZone"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("zone_id")}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_RECORD"
    properties: GCPRecordSetToZoneRelProperties = GCPRecordSetToZoneRelProperties()


@dataclass(frozen=True)
class GCPRecordSetSchema(CartographyNodeSchema):
    label: str = "GCPRecordSet"
    properties: GCPRecordSetNodeProperties = GCPRecordSetNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["DNSRecord"])
    sub_resource_relationship: GCPRecordSetToProjectRel = GCPRecordSetToProjectRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            GCPRecordSetToZoneRel(),
        ]
    )
