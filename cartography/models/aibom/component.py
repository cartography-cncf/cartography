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
    id: PropertyRef = PropertyRef(
        "id",
        description="Stable hash of source key and component occurrence fields.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated.",
    )
    logical_id: PropertyRef = PropertyRef(
        "logical_id",
        extra_index=True,
        description="Stable cross-source fingerprint for equivalent components.",
    )
    name: PropertyRef = PropertyRef("name", description="Detected component name.")
    category: PropertyRef = PropertyRef(
        "category",
        extra_index=True,
        description="Normalized component category used for grouping and filtering.",
    )
    component_type: PropertyRef = PropertyRef(
        "component_type",
        extra_index=True,
        description="AIBOM component type from the report.",
    )
    instance_id: PropertyRef = PropertyRef(
        "instance_id",
        description="AIBOM component instance identifier.",
    )
    file_path: PropertyRef = PropertyRef(
        "file_path",
        description="File path reported for the component.",
    )
    line_number: PropertyRef = PropertyRef(
        "line_number",
        description="Line number reported for the component.",
    )
    model_name: PropertyRef = PropertyRef(
        "model_name",
        description="Model name when the component identifies a concrete model.",
    )
    embedding_model: PropertyRef = PropertyRef(
        "embedding_model",
        description="Embedding model metadata when present.",
    )
    framework: PropertyRef = PropertyRef(
        "framework",
        description="Framework or provider hint emitted by AIBOM.",
    )
    detection_source: PropertyRef = PropertyRef(
        "detection_source",
        extra_index=True,
        description="Detection origin such as code analysis, agentic, or config file.",
    )
    confidence: PropertyRef = PropertyRef(
        "confidence",
        description="Final component confidence.",
    )
    heuristic_confidence: PropertyRef = PropertyRef(
        "heuristic_confidence",
        description="Heuristic confidence from the report.",
    )
    agentic_confidence: PropertyRef = PropertyRef(
        "agentic_confidence",
        description="Agentic confidence from the report.",
    )
    needs_agentic: PropertyRef = PropertyRef(
        "needs_agentic",
        description="Whether the component required agentic review.",
    )
    agentic_hint: PropertyRef = PropertyRef(
        "agentic_hint",
        description="Agentic hint text.",
    )
    description: PropertyRef = PropertyRef(
        "description",
        description="Component description.",
    )
    text: PropertyRef = PropertyRef(
        "text",
        description="Raw component text or value when present.",
    )
    transport: PropertyRef = PropertyRef(
        "transport",
        description="Transport metadata when present.",
    )
    config_source: PropertyRef = PropertyRef(
        "config_source",
        description="Configuration source metadata when present.",
    )
    storage_uri: PropertyRef = PropertyRef(
        "storage_uri",
        description="Storage URI when present.",
    )
    dataset_source: PropertyRef = PropertyRef(
        "dataset_source",
        description="Dataset source metadata when present.",
    )
    skill_format: PropertyRef = PropertyRef(
        "skill_format",
        description="Skill format metadata when present.",
    )
    sdk_version: PropertyRef = PropertyRef(
        "sdk_version",
        description="SDK or package version metadata when present.",
    )
    kb_concept: PropertyRef = PropertyRef(
        "kb_concept",
        description="Knowledge-base concept metadata when present.",
    )
    kb_label: PropertyRef = PropertyRef(
        "kb_label",
        description="Knowledge-base label metadata when present.",
    )
    component_primary_evidence: PropertyRef = PropertyRef(
        "component_primary_evidence",
        description="Primary evidence file path selected for the component.",
    )
    component_primary_evidence_start_line: PropertyRef = PropertyRef(
        "component_primary_evidence_start_line",
        description="Start line of the primary evidence location.",
    )
    component_primary_evidence_end_line: PropertyRef = PropertyRef(
        "component_primary_evidence_end_line",
        description="End line of the primary evidence location.",
    )
    decision: PropertyRef = PropertyRef(
        "decision",
        description="Decision annotation for the component.",
    )
    decision_justification: PropertyRef = PropertyRef(
        "decision_justification",
        description="Justification from the component decision annotation.",
    )
    # Preserve category-specific metadata until we decide whether component types
    # should split into dedicated node models with their own first-class fields.
    metadata_json: PropertyRef = PropertyRef(
        "metadata_json",
        description="Serialized category-specific component metadata.",
    )
    manifest_digests: PropertyRef = PropertyRef(
        "manifest_digests",
        extra_index=True,
        description="Concrete image digests used to link the component to Image nodes.",
    )


@dataclass(frozen=True)
class AIBOMComponentDetectedInRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AIBOMComponentDetectedInRel(CartographyRelSchema):
    """Links a component occurrence to the concrete image where it was detected."""

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
class AIBOMComponentDetectedInGitHubRel(CartographyRelSchema):
    """Links a component occurrence to its scanned GitHub repository."""

    target_node_label: str = "GitHubRepository"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"url": PropertyRef("github_repo_urls", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "DETECTED_IN"
    properties: AIBOMComponentDetectedInRelProperties = (
        AIBOMComponentDetectedInRelProperties()
    )


@dataclass(frozen=True)
class AIBOMComponentDetectedInGitLabRel(CartographyRelSchema):
    """Links a component occurrence to its scanned GitLab project."""

    target_node_label: str = "GitLabProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"web_url": PropertyRef("gitlab_project_urls", one_to_many=True)},
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
    """Links a component to another component that represents a model it uses."""

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
    """Links a component to another component that represents a tool it uses."""

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
    """Links a component to another component that represents an exposed tool."""

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
    """Preserves a custom component relationship emitted by an AIBOM report."""

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
    """One detected AI component occurrence within an AIBOM source."""

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
            AIBOMComponentDetectedInGitHubRel(),
            AIBOMComponentDetectedInGitLabRel(),
            AIBOMComponentUsesModelRel(),
            AIBOMComponentUsesToolRel(),
            AIBOMComponentExposesToolRel(),
            AIBOMComponentCustomRel(),
        ],
    )
