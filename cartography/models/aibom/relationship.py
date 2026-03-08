from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class AIBOMRelationshipNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    relationship_type: PropertyRef = PropertyRef("relationship_type", extra_index=True)
    raw_source_instance_id: PropertyRef = PropertyRef("raw_source_instance_id")
    raw_target_instance_id: PropertyRef = PropertyRef("raw_target_instance_id")
    raw_source_name: PropertyRef = PropertyRef("raw_source_name")
    raw_target_name: PropertyRef = PropertyRef("raw_target_name")
    raw_source_category: PropertyRef = PropertyRef("raw_source_category")
    raw_target_category: PropertyRef = PropertyRef("raw_target_category")


@dataclass(frozen=True)
class AIBOMRelationshipFromComponentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AIBOMRelationshipFromComponentRel(CartographyRelSchema):
    target_node_label: str = "AIBOMComponent"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("source_component_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "FROM_COMPONENT"
    properties: AIBOMRelationshipFromComponentRelProperties = (
        AIBOMRelationshipFromComponentRelProperties()
    )


@dataclass(frozen=True)
class AIBOMRelationshipToComponentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AIBOMRelationshipToComponentRel(CartographyRelSchema):
    target_node_label: str = "AIBOMComponent"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("target_component_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "TO_COMPONENT"
    properties: AIBOMRelationshipToComponentRelProperties = (
        AIBOMRelationshipToComponentRelProperties()
    )


@dataclass(frozen=True)
class AIBOMRelationshipSchema(CartographyNodeSchema):
    label: str = "AIBOMRelationship"
    scoped_cleanup: bool = False
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([])
    properties: AIBOMRelationshipNodeProperties = AIBOMRelationshipNodeProperties()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AIBOMRelationshipFromComponentRel(),
            AIBOMRelationshipToComponentRel(),
        ],
    )
