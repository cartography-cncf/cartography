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
class GCPNetworkTagNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("tag_id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    value: PropertyRef = PropertyRef("value")


@dataclass(frozen=True)
class GCPNetworkTagToVpcRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPNetworkTagToVpcRel(CartographyRelSchema):
    target_node_label: str = "GCPVpc"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("vpc_partial_uri"),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "DEFINED_IN"
    properties: GCPNetworkTagToVpcRelProperties = GCPNetworkTagToVpcRelProperties()


@dataclass(frozen=True)
class GCPNetworkTagToInstanceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPNetworkTagToInstanceRel(CartographyRelSchema):
    target_node_label: str = "GCPInstance"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("instance_partial_uri"),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "TAGGED"
    properties: GCPNetworkTagToInstanceRelProperties = (
        GCPNetworkTagToInstanceRelProperties()
    )


@dataclass(frozen=True)
class GCPNetworkTagToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPNetworkTagToProjectRel(CartographyRelSchema):
    target_node_label: str = "GCPProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("PROJECT_ID", set_in_kwargs=True),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GCPNetworkTagToProjectRelProperties = (
        GCPNetworkTagToProjectRelProperties()
    )


@dataclass(frozen=True)
class GCPNetworkTagSchema(CartographyNodeSchema):
    label: str = "GCPNetworkTag"
    properties: GCPNetworkTagNodeProperties = GCPNetworkTagNodeProperties()
    sub_resource_relationship: GCPNetworkTagToProjectRel = GCPNetworkTagToProjectRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            GCPNetworkTagToVpcRel(),
            GCPNetworkTagToInstanceRel(),
        ]
    )
