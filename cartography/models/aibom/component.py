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
    instance_id: PropertyRef = PropertyRef("instance_id")
    assigned_target: PropertyRef = PropertyRef("assigned_target")
    file_path: PropertyRef = PropertyRef("file_path")
    line_number: PropertyRef = PropertyRef("line_number")
    model_name: PropertyRef = PropertyRef("model_name")
    framework: PropertyRef = PropertyRef("framework")
    label: PropertyRef = PropertyRef("label")
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
class AIBOMComponentInWorkflowRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AIBOMComponentInWorkflowRel(CartographyRelSchema):
    target_node_label: str = "AIBOMWorkflow"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("workflow_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "IN_WORKFLOW"
    properties: AIBOMComponentInWorkflowRelProperties = (
        AIBOMComponentInWorkflowRelProperties()
    )


@dataclass(frozen=True)
class AIBOMComponentToComponentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


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
class AIBOMComponentUsesModelRel(CartographyRelSchema):
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
class AIBOMComponentUsesMemoryRel(CartographyRelSchema):
    target_node_label: str = "AIBOMComponent"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("uses_memory_component_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES_MEMORY"
    properties: AIBOMComponentToComponentRelProperties = (
        AIBOMComponentToComponentRelProperties()
    )


@dataclass(frozen=True)
class AIBOMComponentUsesRetrieverRel(CartographyRelSchema):
    target_node_label: str = "AIBOMComponent"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("uses_retriever_component_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES_RETRIEVER"
    properties: AIBOMComponentToComponentRelProperties = (
        AIBOMComponentToComponentRelProperties()
    )


@dataclass(frozen=True)
class AIBOMComponentUsesEmbeddingRel(CartographyRelSchema):
    target_node_label: str = "AIBOMComponent"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("uses_embedding_component_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES_EMBEDDING"
    properties: AIBOMComponentToComponentRelProperties = (
        AIBOMComponentToComponentRelProperties()
    )


@dataclass(frozen=True)
class AIBOMComponentUsesPromptRel(CartographyRelSchema):
    target_node_label: str = "AIBOMComponent"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("uses_prompt_component_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES_PROMPT"
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
            AIBOMComponentInWorkflowRel(),
            AIBOMComponentUsesToolRel(),
            AIBOMComponentUsesModelRel(),
            AIBOMComponentUsesMemoryRel(),
            AIBOMComponentUsesRetrieverRel(),
            AIBOMComponentUsesEmbeddingRel(),
            AIBOMComponentUsesPromptRel(),
        ],
    )
