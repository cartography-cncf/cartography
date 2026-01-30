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
class InvalidUnscopedNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class InvalidUnscopedToSimpleRelProps(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class InvalidUnscopedToSimpleRel(CartographyRelSchema):
    target_node_label: str = "SimpleNode"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "RELATES_TO"
    properties: InvalidUnscopedToSimpleRelProps = InvalidUnscopedToSimpleRelProps()


@dataclass(frozen=True)
class InvalidUnscopedNodeSchema(CartographyNodeSchema):
    label: str = "InvalidUnscopedNode"
    properties: InvalidUnscopedNodeProperties = InvalidUnscopedNodeProperties()
    # This node has scoped_cleanup=False but also has a sub_resource_relationship
    # which should trigger the ValueError
    scoped_cleanup: bool = False
    sub_resource_relationship: CartographyRelSchema = InvalidUnscopedToSimpleRel()
