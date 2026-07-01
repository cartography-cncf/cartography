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
class ScalewayDnsRecordProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", extra_index=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    type: PropertyRef = PropertyRef("type_")
    data: PropertyRef = PropertyRef("data")
    ttl: PropertyRef = PropertyRef("ttl")
    priority: PropertyRef = PropertyRef("priority")
    comment: PropertyRef = PropertyRef("comment")
    updated_at: PropertyRef = PropertyRef("updated_at")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ScalewayDnsRecordToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayProject)-[:RESOURCE]->(:ScalewayDnsRecord)
class ScalewayDnsRecordToProjectRel(CartographyRelSchema):
    target_node_label: str = "ScalewayProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ScalewayDnsRecordToProjectRelProperties = (
        ScalewayDnsRecordToProjectRelProperties()
    )


@dataclass(frozen=True)
class ScalewayDnsRecordToZoneRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayDnsZone)-[:HAS_RECORD]->(:ScalewayDnsRecord)
class ScalewayDnsRecordToZoneRel(CartographyRelSchema):
    target_node_label: str = "ScalewayDnsZone"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("zone_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_RECORD"
    properties: ScalewayDnsRecordToZoneRelProperties = (
        ScalewayDnsRecordToZoneRelProperties()
    )


@dataclass(frozen=True)
class ScalewayDnsRecordSchema(CartographyNodeSchema):
    label: str = "ScalewayDnsRecord"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["DNSRecord"])
    properties: ScalewayDnsRecordProperties = ScalewayDnsRecordProperties()
    sub_resource_relationship: ScalewayDnsRecordToProjectRel = (
        ScalewayDnsRecordToProjectRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            ScalewayDnsRecordToZoneRel(),
        ]
    )
