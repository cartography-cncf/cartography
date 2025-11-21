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
class UnscopedNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class UnscopedToSimpleRelProps(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class UnscopedToSimpleRel(CartographyRelSchema):
    target_node_label: str = "SimpleNode"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("simple_node_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "RELATES_TO"
    properties: UnscopedToSimpleRelProps = UnscopedToSimpleRelProps()


@dataclass(frozen=True)
class UnscopedNodeSchema(CartographyNodeSchema):
    label: str = "UnscopedNode"
    properties: UnscopedNodeProperties = UnscopedNodeProperties()
    # This node can be cleaned up without being attached as a sub-resource of a parent node.
    scoped_cleanup: bool = False
    # Note that sub-resource relationship is not defined
    other_relationships: OtherRelationships = OtherRelationships(
        rels=[
            UnscopedToSimpleRel(),
        ]
    )
