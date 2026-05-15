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
    scan_scope: PropertyRef = PropertyRef("scan_scope")
    report_location: PropertyRef = PropertyRef("report_location")
    scanner_name: PropertyRef = PropertyRef("scanner_name")
    scanner_version: PropertyRef = PropertyRef("scanner_version")
    analyzer_version: PropertyRef = PropertyRef("analyzer_version")
    analysis_status: PropertyRef = PropertyRef("analysis_status", extra_index=True)
    report_total_sources: PropertyRef = PropertyRef("report_total_sources")
    report_total_components: PropertyRef = PropertyRef("report_total_components")
    report_total_workflows: PropertyRef = PropertyRef("report_total_workflows")
    report_total_relationships: PropertyRef = PropertyRef("report_total_relationships")
    report_category_summary_json: PropertyRef = PropertyRef(
        "report_category_summary_json"
    )
    source_key: PropertyRef = PropertyRef("source_key", extra_index=True)
    source_status: PropertyRef = PropertyRef("source_status", extra_index=True)
    source_kind: PropertyRef = PropertyRef("source_kind", extra_index=True)
    total_components: PropertyRef = PropertyRef("total_components")
    total_workflows: PropertyRef = PropertyRef("total_workflows")
    total_relationships: PropertyRef = PropertyRef("total_relationships")
    category_summary_json: PropertyRef = PropertyRef("category_summary_json")


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
class AIBOMSourceToWorkflowRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AIBOMSourceToWorkflowRel(CartographyRelSchema):
    target_node_label: str = "AIBOMWorkflow"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("workflow_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_WORKFLOW"
    properties: AIBOMSourceToWorkflowRelProperties = (
        AIBOMSourceToWorkflowRelProperties()
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
            AIBOMSourceToComponentRel(),
            AIBOMSourceToWorkflowRel(),
        ],
    )
