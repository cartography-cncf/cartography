from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeSchema, CartographyNodeProperties
from cartography.models.core.relationships import CartographyRelProperties, CartographyRelSchema, TargetNodeMatcher, \
    LinkDirection, make_target_node_matcher, OtherRelationships


# Test defining a simple node with no relationships.
@dataclass(frozen=True)
class NodeAProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef('Id')
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)
    property1: PropertyRef = PropertyRef('property1')
    property2: PropertyRef = PropertyRef('property2')


# Test defining a simple node attached to another node
@dataclass(frozen=True)
class NodeAToNodeBProps(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class NodeAToNodeB(CartographyRelSchema):
    target_node_label: str = 'SimpleNode'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('sub_resource_id', set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "POINTS_TO"
    properties: NodeAToNodeBProps = NodeAToNodeBProps()


@dataclass(frozen=True)
class NodeA(CartographyNodeSchema):
    label: str = 'NodeA'
    properties: NodeAProperties = NodeAProperties()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            NodeAToNodeB(),
        ]
    )
