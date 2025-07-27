from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class GCPVpcNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("partial_uri", extra_index=True)
    lastupdated: PropertyRef = PropertyRef("LASTUPDATED", set_in_kwargs=True)
    partial_uri: PropertyRef = PropertyRef("partial_uri")
    self_link: PropertyRef = PropertyRef("self_link")
    name: PropertyRef = PropertyRef("name", extra_index=True)
    project_id: PropertyRef = PropertyRef("PROJECT_ID", set_in_kwargs=True)
    auto_create_subnetworks: PropertyRef = PropertyRef("auto_create_subnetworks")
    routing_config_routing_mode: PropertyRef = PropertyRef(
        "routing_config_routing_mode"
    )
    description: PropertyRef = PropertyRef("description")


@dataclass(frozen=True)
class GCPVpcToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("LASTUPDATED", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPVpcToProjectRel(CartographyRelSchema):
    target_node_label: str = "GCPProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("PROJECT_ID", set_in_kwargs=True),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GCPVpcToProjectRelProperties = GCPVpcToProjectRelProperties()


@dataclass(frozen=True)
class GCPVpcSchema(CartographyNodeSchema):
    label: str = "GCPVpc"
    properties: GCPVpcNodeProperties = GCPVpcNodeProperties()
    sub_resource_relationship: GCPVpcToProjectRel = GCPVpcToProjectRel()
