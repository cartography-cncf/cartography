from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ConditionalNodeLabel
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class AIBOMComponentNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    logical_id: PropertyRef = PropertyRef("logical_id", extra_index=True)
    name: PropertyRef = PropertyRef("name")
    category: PropertyRef = PropertyRef("category", extra_index=True)
    component_type: PropertyRef = PropertyRef("component_type", extra_index=True)
    instance_id: PropertyRef = PropertyRef("instance_id")
    file_path: PropertyRef = PropertyRef("file_path")
    line_number: PropertyRef = PropertyRef("line_number")
    model_name: PropertyRef = PropertyRef("model_name")
    embedding_model: PropertyRef = PropertyRef("embedding_model")
    framework: PropertyRef = PropertyRef("framework")
    detection_source: PropertyRef = PropertyRef("detection_source", extra_index=True)
    confidence: PropertyRef = PropertyRef("confidence")
    heuristic_confidence: PropertyRef = PropertyRef("heuristic_confidence")
    agentic_confidence: PropertyRef = PropertyRef("agentic_confidence")
    needs_agentic: PropertyRef = PropertyRef("needs_agentic")
    agentic_hint: PropertyRef = PropertyRef("agentic_hint")
    description: PropertyRef = PropertyRef("description")
    text: PropertyRef = PropertyRef("text")
    transport: PropertyRef = PropertyRef("transport")
    config_source: PropertyRef = PropertyRef("config_source")
    storage_uri: PropertyRef = PropertyRef("storage_uri")
    dataset_source: PropertyRef = PropertyRef("dataset_source")
    skill_format: PropertyRef = PropertyRef("skill_format")
    sdk_version: PropertyRef = PropertyRef("sdk_version")
    kb_concept: PropertyRef = PropertyRef("kb_concept")
    kb_label: PropertyRef = PropertyRef("kb_label")
    component_primary_evidence: PropertyRef = PropertyRef("component_primary_evidence")
    component_primary_evidence_start_line: PropertyRef = PropertyRef(
        "component_primary_evidence_start_line"
    )
    component_primary_evidence_end_line: PropertyRef = PropertyRef(
        "component_primary_evidence_end_line"
    )
    decision: PropertyRef = PropertyRef("decision")
    decision_justification: PropertyRef = PropertyRef("decision_justification")
    # Preserve category-specific metadata until we decide whether component types
    # should split into dedicated node models with their own first-class fields.
    metadata_json: PropertyRef = PropertyRef("metadata_json")
    manifest_digests: PropertyRef = PropertyRef("manifest_digests", extra_index=True)


@dataclass(frozen=True)
class AIBOMComponentDetectedInRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AIBOMComponentDetectedInRel(CartographyRelSchema):
    target_node_label: str = "Image"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"_ont_digest": PropertyRef("manifest_digests", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "DETECTED_IN"
    properties: AIBOMComponentDetectedInRelProperties = (
        AIBOMComponentDetectedInRelProperties()
    )


@dataclass(frozen=True)
class AIBOMComponentToComponentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AIBOMComponentUsesModelRel(CartographyRelSchema):
    # These arrays should contain resolved AIBOMComponent.id values built during
    # transform, not raw report-side identifiers. The current report links
    # components by source-scoped type/name and does not provide stable edge ids.
    target_node_label: str = "AIBOMComponent"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("uses_model_component_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES_MODEL"
    properties: AIBOMComponentToComponentRelProperties = (
        AIBOMComponentToComponentRelProperties()
    )


@dataclass(frozen=True)
class AIBOMComponentUsesToolRel(CartographyRelSchema):
    target_node_label: str = "AIBOMComponent"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("uses_tool_component_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES_TOOL"
    properties: AIBOMComponentToComponentRelProperties = (
        AIBOMComponentToComponentRelProperties()
    )


@dataclass(frozen=True)
class AIBOMComponentExposesToolRel(CartographyRelSchema):
    target_node_label: str = "AIBOMComponent"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("exposes_tool_component_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "EXPOSES_TOOL"
    properties: AIBOMComponentToComponentRelProperties = (
        AIBOMComponentToComponentRelProperties()
    )


@dataclass(frozen=True)
class AIBOMComponentCustomRel(CartographyRelSchema):
    target_node_label: str = "AIBOMComponent"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("custom_component_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "CUSTOM"
    properties: AIBOMComponentToComponentRelProperties = (
        AIBOMComponentToComponentRelProperties()
    )


@dataclass(frozen=True)
class AIBOMComponentSchema(CartographyNodeSchema):
    label: str = "AIBOMComponent"
    scoped_cleanup: bool = False
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        [
            ConditionalNodeLabel(label="AIAgent", conditions={"category": "agent"}),
            ConditionalNodeLabel(label="AIModel", conditions={"category": "model"}),
            ConditionalNodeLabel(label="AITool", conditions={"category": "tool"}),
            ConditionalNodeLabel(label="AIMemory", conditions={"category": "memory"}),
            ConditionalNodeLabel(
                label="AIEmbedding",
                conditions={"category": "embedding"},
            ),
            ConditionalNodeLabel(label="AIPrompt", conditions={"category": "prompt"}),
        ],
    )
    properties: AIBOMComponentNodeProperties = AIBOMComponentNodeProperties()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AIBOMComponentDetectedInRel(),
            AIBOMComponentUsesModelRel(),
            AIBOMComponentUsesToolRel(),
            AIBOMComponentExposesToolRel(),
            AIBOMComponentCustomRel(),
        ],
    )
