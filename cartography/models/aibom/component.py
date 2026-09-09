from dataclasses import dataclass

from cartography.models.aibom.extra_labels import LEGACY_AI_MODEL
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
from cartography.models.ontology.labels import AI_AGENT
from cartography.models.ontology.labels import AI_EMBEDDING
from cartography.models.ontology.labels import AI_MEMORY
from cartography.models.ontology.labels import AI_MODEL_REFERENCE
from cartography.models.ontology.labels import AI_PROMPT
from cartography.models.ontology.labels import AI_TOOL


@dataclass(frozen=True)
class AIBOMComponentNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Stable hash of source key and component occurrence fields.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    logical_id: PropertyRef = PropertyRef(
        "logical_id",
        extra_index=True,
        description="Stable cross-source fingerprint for equivalent components.",
    )
    name: PropertyRef = PropertyRef("name", description="Detected component name.")
    component_type: PropertyRef = PropertyRef(
        "component_type",
        extra_index=True,
        description=(
            "AIBOM component type from the report, and the value that decides the "
            "component's semantic label: agent, model, tool, memory, embedding, or prompt."
        ),
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
        description="Model name. Set on model components, and on other types that name a concrete model.",
    )
    embedding_model: PropertyRef = PropertyRef(
        "embedding_model",
        description="Embedding model metadata. Set on embedding components.",
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
        description="Transport metadata. Set on tool components, such as an MCP server's transport.",
    )
    config_source: PropertyRef = PropertyRef(
        "config_source",
        description="Configuration source metadata. Set on components detected from a config file.",
    )
    storage_uri: PropertyRef = PropertyRef(
        "storage_uri",
        description="Storage URI. Set on memory and embedding components.",
    )
    dataset_source: PropertyRef = PropertyRef(
        "dataset_source",
        description="Dataset source metadata. Set on embedding and memory components.",
    )
    skill_format: PropertyRef = PropertyRef(
        "skill_format",
        description="Skill format metadata. Set on tool components.",
    )
    sdk_version: PropertyRef = PropertyRef(
        "sdk_version",
        description="SDK or package version metadata when present.",
    )
    kb_concept: PropertyRef = PropertyRef(
        "kb_concept",
        description="Knowledge-base concept metadata. Set on components detected by knowledge-base enrichment.",
    )
    kb_label: PropertyRef = PropertyRef(
        "kb_label",
        description="Knowledge-base label metadata. Set on components detected by knowledge-base enrichment.",
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
    evidence_count: PropertyRef = PropertyRef(
        "evidence_count",
        description="How many places in the artifact the detection was seen.",
    )
    evidence_files: PropertyRef = PropertyRef(
        "evidence_files",
        description=(
            "Every file the detection was seen in. `file_path` and "
            "`component_primary_evidence` name one of these; this is the full set."
        ),
    )
    # Type-specific metadata stays serialized until component types split into
    # dedicated node models with their own first-class fields. Anything promoted out
    # of here becomes queryable, so promote a key once it is worth filtering on
    # rather than adding every key a report can emit.
    metadata_json: PropertyRef = PropertyRef(
        "metadata_json",
        description=(
            "Serialized type-specific component metadata that has no first-class "
            "property yet. Keys vary by component_type: a secret component carries "
            "secret_source and redacted, a package component carries ecosystem and "
            "vulnerabilities, a model component carries model_provider and "
            "context_length. Read it in the client; it is a string, not a map."
        ),
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
class AIBOMComponentUsesLlmRel(CartographyRelSchema):
    """Links a component to a model it uses, where the report typed the edge as an LLM."""

    target_node_label: str = "AIBOMComponent"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("uses_llm_component_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES_LLM"
    properties: AIBOMComponentToComponentRelProperties = (
        AIBOMComponentToComponentRelProperties()
    )


@dataclass(frozen=True)
class AIBOMComponentUsesMemoryRel(CartographyRelSchema):
    """Links a component to a memory store it uses."""

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
class AIBOMComponentUsesEmbeddingRel(CartographyRelSchema):
    """Links a component to an embedding it uses."""

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
class AIBOMComponentUsesAgentRel(CartographyRelSchema):
    """Links an agent to another agent it invokes or delegates to."""

    target_node_label: str = "AIBOMComponent"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("uses_agent_component_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES_AGENT"
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
            AI_AGENT.when(component_type="agent"),
            AI_MODEL_REFERENCE.when(component_type="model"),
            LEGACY_AI_MODEL.when(component_type="model"),
            AI_TOOL.when(component_type="tool"),
            AI_MEMORY.when(component_type="memory"),
            AI_EMBEDDING.when(component_type="embedding"),
            AI_PROMPT.when(component_type="prompt"),
        ],
    )
    properties: AIBOMComponentNodeProperties = AIBOMComponentNodeProperties()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AIBOMComponentDetectedInRel(),
            AIBOMComponentDetectedInGitHubRel(),
            AIBOMComponentDetectedInGitLabRel(),
            AIBOMComponentUsesModelRel(),
            AIBOMComponentUsesLlmRel(),
            AIBOMComponentUsesToolRel(),
            AIBOMComponentExposesToolRel(),
            AIBOMComponentUsesMemoryRel(),
            AIBOMComponentUsesEmbeddingRel(),
            AIBOMComponentUsesAgentRel(),
            AIBOMComponentCustomRel(),
        ],
    )
