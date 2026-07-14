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
class AIBOMSourceNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Stable hash of the source key.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated.",
    )
    image_uri: PropertyRef = PropertyRef(
        "image_uri",
        extra_index=True,
        description="Source image URI, falling back to the source key.",
    )
    manifest_digests: PropertyRef = PropertyRef(
        "manifest_digests",
        extra_index=True,
        description="Concrete image digests extracted from the source key.",
    )
    image_matched: PropertyRef = PropertyRef(
        "image_matched",
        extra_index=True,
        description="Whether the source carried a digest-qualified image anchor.",
    )
    report_location: PropertyRef = PropertyRef(
        "report_location",
        description="Local path or object-store URI used for ingestion.",
    )
    run_id: PropertyRef = PropertyRef(
        "run_id",
        extra_index=True,
        description="Report run identifier.",
    )
    analyzer_version: PropertyRef = PropertyRef(
        "analyzer_version",
        description="AIBOM analyzer version.",
    )
    analysis_status: PropertyRef = PropertyRef(
        "analysis_status",
        extra_index=True,
        description="Top-level report status.",
    )
    report_schema_version: PropertyRef = PropertyRef(
        "report_schema_version",
        extra_index=True,
        description="AIBOM report schema version.",
    )
    report_started_at: PropertyRef = PropertyRef(
        "report_started_at",
        description="Report start timestamp.",
    )
    report_completed_at: PropertyRef = PropertyRef(
        "report_completed_at",
        description="Report completion timestamp.",
    )
    report_output_format: PropertyRef = PropertyRef(
        "report_output_format",
        description="Output format reported by AIBOM.",
    )
    llm_model: PropertyRef = PropertyRef(
        "llm_model",
        description="LLM model used during analysis when present.",
    )
    sources_requested: PropertyRef = PropertyRef(
        "sources_requested",
        description="Number of requested sources in the report.",
    )
    sources_analyzed: PropertyRef = PropertyRef(
        "sources_analyzed",
        description="Number of analyzed sources in the report.",
    )
    sources_with_errors: PropertyRef = PropertyRef(
        "sources_with_errors",
        description="Number of sources with errors in the report.",
    )
    error_count: PropertyRef = PropertyRef(
        "error_count",
        description="Total report error count.",
    )
    prompt_tokens: PropertyRef = PropertyRef(
        "prompt_tokens",
        description="Top-level prompt token count.",
    )
    completion_tokens: PropertyRef = PropertyRef(
        "completion_tokens",
        description="Top-level completion token count.",
    )
    total_tokens: PropertyRef = PropertyRef(
        "total_tokens",
        description="Top-level total token count.",
    )
    report_total_sources: PropertyRef = PropertyRef(
        "report_total_sources",
        description="Top-level summary source count.",
    )
    report_total_components: PropertyRef = PropertyRef(
        "report_total_components",
        description="Top-level summary component count.",
    )
    report_total_relationships: PropertyRef = PropertyRef(
        "report_total_relationships",
        description="Top-level summary relationship count.",
    )
    pending_agent_review: PropertyRef = PropertyRef(
        "pending_agent_review",
        description="Top-level summary pending review count.",
    )
    test_only_components: PropertyRef = PropertyRef(
        "test_only_components",
        description="Top-level summary test-only component count.",
    )
    report_component_types: PropertyRef = PropertyRef(
        "report_component_types",
        description="Sorted list of top-level component categories.",
    )
    report_component_type_counts: PropertyRef = PropertyRef(
        "report_component_type_counts",
        description="Counts corresponding to the top-level component categories.",
    )
    risk_score: PropertyRef = PropertyRef(
        "risk_score",
        description="Top-level risk score.",
    )
    risk_severity: PropertyRef = PropertyRef(
        "risk_severity",
        extra_index=True,
        description="Top-level risk severity.",
    )
    source_key: PropertyRef = PropertyRef(
        "source_key",
        extra_index=True,
        description="Native source key emitted by AIBOM.",
    )
    source_name: PropertyRef = PropertyRef(
        "source_name",
        description="Source name, falling back to the source key.",
    )
    source_path: PropertyRef = PropertyRef(
        "source_path",
        description="Extracted filesystem path used during scanning.",
    )
    source_status: PropertyRef = PropertyRef(
        "source_status",
        extra_index=True,
        description="Source processing status.",
    )
    source_kind: PropertyRef = PropertyRef(
        "source_kind",
        extra_index=True,
        description="Source kind, such as container or repository.",
    )
    total_components: PropertyRef = PropertyRef(
        "total_components",
        description="Source-level component count.",
    )
    total_relationships: PropertyRef = PropertyRef(
        "total_relationships",
        description="Source-level relationship count.",
    )
    assets_discovered: PropertyRef = PropertyRef(
        "assets_discovered",
        description="Source-level discovered asset count.",
    )
    last_generated_at: PropertyRef = PropertyRef(
        "last_generated_at",
        description="Source generation timestamp.",
    )
    source_elapsed_s: PropertyRef = PropertyRef(
        "source_elapsed_s",
        description="Source-level elapsed time in seconds.",
    )
    source_prompt_tokens: PropertyRef = PropertyRef(
        "source_prompt_tokens",
        description="Source-level prompt token count.",
    )
    source_completion_tokens: PropertyRef = PropertyRef(
        "source_completion_tokens",
        description="Source-level completion token count.",
    )
    source_total_tokens: PropertyRef = PropertyRef(
        "source_total_tokens",
        description="Source-level total token count.",
    )
    source_component_types: PropertyRef = PropertyRef(
        "source_component_types",
        description="Sorted list of component categories in this source.",
    )
    source_component_type_counts: PropertyRef = PropertyRef(
        "source_component_type_counts",
        description="Counts corresponding to this source's component categories.",
    )


@dataclass(frozen=True)
class AIBOMSourceToImageRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AIBOMSourceToImageRel(CartographyRelSchema):
    """Links an AIBOM source to the concrete image it scanned."""

    target_node_label: str = "Image"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"_ont_digest": PropertyRef("manifest_digests", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "SCANNED_IMAGE"
    properties: AIBOMSourceToImageRelProperties = AIBOMSourceToImageRelProperties()


@dataclass(frozen=True)
class AIBOMSourceToGitHubRepoRel(CartographyRelSchema):
    """Links an AIBOM source to the GitHub repository it scanned."""

    target_node_label: str = "GitHubRepository"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"url": PropertyRef("github_repo_urls", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "SCANNED_REPOSITORY"
    properties: AIBOMSourceToImageRelProperties = AIBOMSourceToImageRelProperties()


@dataclass(frozen=True)
class AIBOMSourceToGitLabProjectRel(CartographyRelSchema):
    """Links an AIBOM source to the GitLab project it scanned."""

    target_node_label: str = "GitLabProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"web_url": PropertyRef("gitlab_project_urls", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "SCANNED_REPOSITORY"
    properties: AIBOMSourceToImageRelProperties = AIBOMSourceToImageRelProperties()


@dataclass(frozen=True)
class AIBOMSourceToComponentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AIBOMSourceToComponentRel(CartographyRelSchema):
    """Links an AIBOM source to its detected component occurrences."""

    target_node_label: str = "AIBOMComponent"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("component_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_COMPONENT"
    properties: AIBOMSourceToComponentRelProperties = (
        AIBOMSourceToComponentRelProperties()
    )


@dataclass(frozen=True)
class AIBOMSourceSchema(CartographyNodeSchema):
    """One scanned image or repository represented in an AIBOM report."""

    label: str = "AIBOMSource"
    scoped_cleanup: bool = False
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([])
    properties: AIBOMSourceNodeProperties = AIBOMSourceNodeProperties()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AIBOMSourceToImageRel(),
            AIBOMSourceToGitHubRepoRel(),
            AIBOMSourceToGitLabProjectRel(),
            AIBOMSourceToComponentRel(),
        ],
    )
