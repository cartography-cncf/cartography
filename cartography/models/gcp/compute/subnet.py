from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class GCPSubnetNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("partial_uri", extra_index=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    partial_uri: PropertyRef = PropertyRef("partial_uri")
    self_link: PropertyRef = PropertyRef("self_link")
    name: PropertyRef = PropertyRef("name", extra_index=True)
    project_id: PropertyRef = PropertyRef("project_id")
    region: PropertyRef = PropertyRef("region")
    gateway_address: PropertyRef = PropertyRef("gateway_address")
    ip_cidr_range: PropertyRef = PropertyRef("ip_cidr_range")
    private_ip_google_access: PropertyRef = PropertyRef("private_ip_google_access")
    vpc_partial_uri: PropertyRef = PropertyRef("vpc_partial_uri")


@dataclass(frozen=True)
class GCPSubnetToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPSubnetToProjectRel(CartographyRelSchema):
    target_node_label: str = "GCPProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("PROJECT_ID", set_in_kwargs=True),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GCPSubnetToProjectRelProperties = GCPSubnetToProjectRelProperties()


@dataclass(frozen=True)
class GCPSubnetToVpcRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPSubnetToVpcRel(CartographyRelSchema):
    target_node_label: str = "GCPVpc"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("vpc_partial_uri"),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS"
    properties: GCPSubnetToVpcRelProperties = GCPSubnetToVpcRelProperties()


@dataclass(frozen=True)
class GCPSubnetSchema(CartographyNodeSchema):
    label: str = "GCPSubnet"
    properties: GCPSubnetNodeProperties = GCPSubnetNodeProperties()
    sub_resource_relationship: GCPSubnetToProjectRel = GCPSubnetToProjectRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            GCPSubnetToVpcRel(),
        ]
    )
