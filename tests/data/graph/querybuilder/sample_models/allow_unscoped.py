from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties, OtherRelationships
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher
from tests.data.graph.querybuilder.sample_models.simple_node import SimpleNodeSchema


@dataclass(frozen=True)
class UnscopedNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("Id")
    name: PropertyRef = PropertyRef("name")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class UnscopedToSimpleRelProps(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class UnscopedToSimpleRel(CartographyRelSchema):
    target_node_label: str = "SimpleNode"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "RELATES_TO"
    properties: UnscopedToSimpleRelProps = UnscopedToSimpleRelProps()


@dataclass(frozen=True)
class UnscopedNodeSchema(CartographyNodeSchema):
    label: str = "UnscopedNode"
    properties: UnscopedNodeProperties = UnscopedNodeProperties()
    # This node can be cleaned up without being attached to a sub-resource
    scoped_cleanup: bool = False
    # No sub-resource relationship defined
    sub_resource_relationship: CartographyRelSchema = None
    other_relationships: OtherRelationships = OtherRelationships(rels=[
        UnscopedToSimpleRel(),
    ])
