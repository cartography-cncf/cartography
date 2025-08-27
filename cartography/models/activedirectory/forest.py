from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties, CartographyNodeSchema
from cartography.models.core.relationships import (
    CartographyRelProperties,
    CartographyRelSchema,
    LinkDirection,
    OtherRelationships,
    TargetNodeMatcher,
    make_target_node_matcher,
)


@dataclass(frozen=True)
class ADForestNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    functional_level: PropertyRef = PropertyRef("functional_level")


@dataclass(frozen=True)
class ADForestSchema(CartographyNodeSchema):
    label: str = "ADForest"
    properties: ADForestNodeProperties = ADForestNodeProperties()
    # Forest is top-level; no sub_resource_relationship
    # Explicitly mark as global cleanup
    scoped_cleanup: bool = False

