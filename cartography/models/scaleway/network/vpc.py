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
class ScalewayVpcProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name")
    region: PropertyRef = PropertyRef("region")
    tags: PropertyRef = PropertyRef("tags")
    is_default: PropertyRef = PropertyRef("is_default")
    private_network_count: PropertyRef = PropertyRef("private_network_count")
    routing_enabled: PropertyRef = PropertyRef("routing_enabled")
    custom_routes_propagation_enabled: PropertyRef = PropertyRef(
        "custom_routes_propagation_enabled"
    )
    created_at: PropertyRef = PropertyRef("created_at")
    updated_at: PropertyRef = PropertyRef("updated_at")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ScalewayVpcToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayProject)-[:RESOURCE]->(:ScalewayVpc)
class ScalewayVpcToProjectRel(CartographyRelSchema):
    target_node_label: str = "ScalewayProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ScalewayVpcToProjectRelProperties = ScalewayVpcToProjectRelProperties()


@dataclass(frozen=True)
class ScalewayVpcSchema(CartographyNodeSchema):
    label: str = "ScalewayVpc"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["VirtualNetwork"])
    properties: ScalewayVpcProperties = ScalewayVpcProperties()
    sub_resource_relationship: ScalewayVpcToProjectRel = ScalewayVpcToProjectRel()
