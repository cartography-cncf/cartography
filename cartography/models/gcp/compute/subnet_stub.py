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
class GCPSubnetStubNodeProperties(CartographyNodeProperties):
    """
    Minimal properties for GCPSubnet stub nodes.
    These are created to ensure PART_OF_SUBNET relationships can be established
    even before the full subnet data is loaded.
    """

    id: PropertyRef = PropertyRef("partial_uri")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    partial_uri: PropertyRef = PropertyRef("partial_uri", extra_index=True)


@dataclass(frozen=True)
class GCPSubnetStubToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPSubnetStubToProjectRel(CartographyRelSchema):
    target_node_label: str = "GCPProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("PROJECT_ID", set_in_kwargs=True),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GCPSubnetStubToProjectRelProperties = (
        GCPSubnetStubToProjectRelProperties()
    )


@dataclass(frozen=True)
class GCPSubnetStubSchema(CartographyNodeSchema):
    """
    Schema for creating minimal GCPSubnet stub nodes.
    Used to ensure the subnet node exists before creating relationships to it.
    """

    label: str = "GCPSubnet"
    properties: GCPSubnetStubNodeProperties = GCPSubnetStubNodeProperties()
    sub_resource_relationship: GCPSubnetStubToProjectRel = GCPSubnetStubToProjectRel()
