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
class AIBOMScanNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    image_uri: PropertyRef = PropertyRef("image_uri", extra_index=True)
    manifest_digest: PropertyRef = PropertyRef("manifest_digest", extra_index=True)
    image_matched: PropertyRef = PropertyRef("image_matched", extra_index=True)
    scan_scope: PropertyRef = PropertyRef("scan_scope")
    report_location: PropertyRef = PropertyRef("report_location")
    scanner_name: PropertyRef = PropertyRef("scanner_name")
    scanner_version: PropertyRef = PropertyRef("scanner_version")
    analyzer_version: PropertyRef = PropertyRef("analyzer_version")
    analysis_status: PropertyRef = PropertyRef("analysis_status", extra_index=True)
    total_sources: PropertyRef = PropertyRef("total_sources")
    total_components: PropertyRef = PropertyRef("total_components")
    total_workflows: PropertyRef = PropertyRef("total_workflows")
    total_relationships: PropertyRef = PropertyRef("total_relationships")
    category_summary_json: PropertyRef = PropertyRef("category_summary_json")


@dataclass(frozen=True)
class AIBOMScanScannedImageRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AIBOMScanScannedImageRel(CartographyRelSchema):
    target_node_label: str = "ECRImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"digest": PropertyRef("manifest_digest")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "SCANNED_IMAGE"
    properties: AIBOMScanScannedImageRelProperties = (
        AIBOMScanScannedImageRelProperties()
    )


@dataclass(frozen=True)
class AIBOMScanSchema(CartographyNodeSchema):
    label: str = "AIBOMScan"
    scoped_cleanup: bool = False
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([])
    properties: AIBOMScanNodeProperties = AIBOMScanNodeProperties()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AIBOMScanScannedImageRel(),
        ],
    )
