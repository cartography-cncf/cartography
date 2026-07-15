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
class ScalewayAppleSiliconServerProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name")
    type: PropertyRef = PropertyRef("type_")
    tags: PropertyRef = PropertyRef("tags")
    status: PropertyRef = PropertyRef("status")
    ip: PropertyRef = PropertyRef("ip")
    vpc_status: PropertyRef = PropertyRef("vpc_status")
    public_bandwidth_bps: PropertyRef = PropertyRef("public_bandwidth_bps")
    deletion_scheduled: PropertyRef = PropertyRef("deletion_scheduled")
    delivered: PropertyRef = PropertyRef("delivered")
    zone: PropertyRef = PropertyRef("zone")
    created_at: PropertyRef = PropertyRef("created_at")
    updated_at: PropertyRef = PropertyRef("updated_at")
    deletable_at: PropertyRef = PropertyRef("deletable_at")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ScalewayAppleSiliconServerToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayProject)-[:RESOURCE]->(:ScalewayAppleSiliconServer)
class ScalewayAppleSiliconServerToProjectRel(CartographyRelSchema):
    target_node_label: str = "ScalewayProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ScalewayAppleSiliconServerToProjectRelProperties = (
        ScalewayAppleSiliconServerToProjectRelProperties()
    )


@dataclass(frozen=True)
class ScalewayAppleSiliconServerSchema(CartographyNodeSchema):
    label: str = "ScalewayAppleSiliconServer"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["ComputeInstance"])
    properties: ScalewayAppleSiliconServerProperties = (
        ScalewayAppleSiliconServerProperties()
    )
    sub_resource_relationship: ScalewayAppleSiliconServerToProjectRel = (
        ScalewayAppleSiliconServerToProjectRel()
    )
