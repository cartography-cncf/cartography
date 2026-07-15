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
    id: PropertyRef = PropertyRef(
        "id", extra_index=True, description="Record unique ID."
    )
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Record name (relative to its zone)."
    )
    type: PropertyRef = PropertyRef(
        "type_", description="Record type (`a`, `aaaa`, `cname`, `mx`, ...)."
    )
    data: PropertyRef = PropertyRef(
        "data", description="Record data (target IP, hostname, value, ...)."
    )
    ttl: PropertyRef = PropertyRef("ttl", description="Record TTL in seconds.")
    priority: PropertyRef = PropertyRef(
        "priority", description="Record priority (relevant for MX/SRV)."
    )
    comment: PropertyRef = PropertyRef(
        "comment", description="Free-form record comment."
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at", description="Record last update date."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated", set_in_kwargs=True, description="Timestamp of the last update"
    )


@dataclass(frozen=True)
class ScalewayDnsRecordToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayProject)-[:RESOURCE]->(:ScalewayDnsRecord)
class ScalewayDnsRecordToProjectRel(CartographyRelSchema):
    """Connects `ScalewayProject` to `ScalewayDnsRecord` through `RESOURCE`."""

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
    """Connects `ScalewayDnsZone` to `ScalewayDnsRecord` through `HAS_RECORD`."""

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
    """Represents an individual DNS record within a `ScalewayDnsZone`."""

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
