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
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    image_uri: PropertyRef = PropertyRef("image_uri", extra_index=True)
    manifest_digests: PropertyRef = PropertyRef("manifest_digests", extra_index=True)
    image_matched: PropertyRef = PropertyRef("image_matched", extra_index=True)
    report_location: PropertyRef = PropertyRef("report_location")
    run_id: PropertyRef = PropertyRef("run_id", extra_index=True)
    analyzer_version: PropertyRef = PropertyRef("analyzer_version")
    analysis_status: PropertyRef = PropertyRef("analysis_status", extra_index=True)
    report_schema_version: PropertyRef = PropertyRef(
        "report_schema_version",
        extra_index=True,
    )
    report_started_at: PropertyRef = PropertyRef("report_started_at")
    report_completed_at: PropertyRef = PropertyRef("report_completed_at")
    report_output_format: PropertyRef = PropertyRef("report_output_format")
    llm_model: PropertyRef = PropertyRef("llm_model")
    sources_requested: PropertyRef = PropertyRef("sources_requested")
    sources_analyzed: PropertyRef = PropertyRef("sources_analyzed")
    sources_with_errors: PropertyRef = PropertyRef("sources_with_errors")
    error_count: PropertyRef = PropertyRef("error_count")
    prompt_tokens: PropertyRef = PropertyRef("prompt_tokens")
    completion_tokens: PropertyRef = PropertyRef("completion_tokens")
    total_tokens: PropertyRef = PropertyRef("total_tokens")
    report_total_sources: PropertyRef = PropertyRef("report_total_sources")
    report_total_components: PropertyRef = PropertyRef("report_total_components")
    report_total_relationships: PropertyRef = PropertyRef("report_total_relationships")
    pending_agent_review: PropertyRef = PropertyRef("pending_agent_review")
    test_only_components: PropertyRef = PropertyRef("test_only_components")
    report_component_types: PropertyRef = PropertyRef("report_component_types")
    report_component_type_counts: PropertyRef = PropertyRef(
        "report_component_type_counts"
    )
    risk_score: PropertyRef = PropertyRef("risk_score")
    risk_severity: PropertyRef = PropertyRef("risk_severity", extra_index=True)
    source_key: PropertyRef = PropertyRef("source_key", extra_index=True)
    source_name: PropertyRef = PropertyRef("source_name")
    source_path: PropertyRef = PropertyRef("source_path")
    source_status: PropertyRef = PropertyRef("source_status", extra_index=True)
    source_kind: PropertyRef = PropertyRef("source_kind", extra_index=True)
    total_components: PropertyRef = PropertyRef("total_components")
    total_relationships: PropertyRef = PropertyRef("total_relationships")
    assets_discovered: PropertyRef = PropertyRef("assets_discovered")
    last_generated_at: PropertyRef = PropertyRef("last_generated_at")
    source_elapsed_s: PropertyRef = PropertyRef("source_elapsed_s")
    source_prompt_tokens: PropertyRef = PropertyRef("source_prompt_tokens")
    source_completion_tokens: PropertyRef = PropertyRef("source_completion_tokens")
    source_total_tokens: PropertyRef = PropertyRef("source_total_tokens")
    source_component_types: PropertyRef = PropertyRef("source_component_types")
    source_component_type_counts: PropertyRef = PropertyRef(
        "source_component_type_counts"
    )


@dataclass(frozen=True)
class AIBOMSourceToImageRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AIBOMSourceToImageRel(CartographyRelSchema):
    target_node_label: str = "Image"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"_ont_digest": PropertyRef("manifest_digests", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "SCANNED_IMAGE"
    properties: AIBOMSourceToImageRelProperties = AIBOMSourceToImageRelProperties()


@dataclass(frozen=True)
class AIBOMSourceToGitHubRepoRel(CartographyRelSchema):
    target_node_label: str = "GitHubRepository"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"url": PropertyRef("github_repo_urls", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "SCANNED_REPOSITORY"
    properties: AIBOMSourceToImageRelProperties = AIBOMSourceToImageRelProperties()


@dataclass(frozen=True)
class AIBOMSourceToGitLabProjectRel(CartographyRelSchema):
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
