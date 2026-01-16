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
class S1AppFindingNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", extra_index=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)

    # CVE specific
    cve_id: PropertyRef = PropertyRef("cve_id", extra_index=True)
    severity: PropertyRef = PropertyRef("severity")

    # Instance specific (Finding)
    days_detected: PropertyRef = PropertyRef("days_detected")
    detection_date: PropertyRef = PropertyRef("detection_date")
    last_scan_date: PropertyRef = PropertyRef("last_scan_date")
    last_scan_result: PropertyRef = PropertyRef("last_scan_result")
    status: PropertyRef = PropertyRef("status")
    mitigation_status: PropertyRef = PropertyRef("mitigation_status")
    mitigation_status_reason: PropertyRef = PropertyRef("mitigation_status_reason")
    mitigation_status_changed_by: PropertyRef = PropertyRef(
        "mitigation_status_changed_by"
    )
    mitigation_status_change_time: PropertyRef = PropertyRef(
        "mitigation_status_change_time"
    )
    marked_by: PropertyRef = PropertyRef("marked_by")
    marked_date: PropertyRef = PropertyRef("marked_date")
    mark_type_description: PropertyRef = PropertyRef("mark_type_description")
    reason: PropertyRef = PropertyRef("reason")
    remediation_level: PropertyRef = PropertyRef("remediation_level")
    risk_score: PropertyRef = PropertyRef("risk_score")
    report_confidence: PropertyRef = PropertyRef("report_confidence")


@dataclass(frozen=True)
class S1AppFindingToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:S1AppFinding)<-[:RESOURCE]-(:S1Account)
class S1AppFindingToAccountRel(CartographyRelSchema):
    target_node_label: str = "S1Account"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("S1_ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: S1AppFindingToAccountRelProperties = (
        S1AppFindingToAccountRelProperties()
    )


@dataclass(frozen=True)
class S1AppFindingToApplicationVersionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:S1AppFinding)-[:AFFECTS]->(:S1ApplicationVersion)
class S1AppFindingToApplicationVersionRel(CartographyRelSchema):
    target_node_label: str = "S1ApplicationVersion"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("application_version_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "AFFECTS"
    properties: S1AppFindingToApplicationVersionRelProperties = (
        S1AppFindingToApplicationVersionRelProperties()
    )


@dataclass(frozen=True)
class S1AppFindingToAgentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:S1AppFinding)-[:AFFECTS]->(:S1Agent)
class S1AppFindingToAgentRel(CartographyRelSchema):
    target_node_label: str = "S1Agent"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("endpoint_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "AFFECTS"
    properties: S1AppFindingToAgentRelProperties = S1AppFindingToAgentRelProperties()


@dataclass(frozen=True)
class S1AppFindingToCVERelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:S1AppFinding)-[:LINKED_TO]->(:CVE)
class S1AppFindingToCVERel(CartographyRelSchema):
    target_node_label: str = "CVE"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("cve_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "LINKED_TO"
    properties: S1AppFindingToCVERelProperties = S1AppFindingToCVERelProperties()


@dataclass(frozen=True)
class S1AppFindingSchema(CartographyNodeSchema):
    label: str = "S1AppFinding"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["S1Finding", "Risk"])
    properties: S1AppFindingNodeProperties = S1AppFindingNodeProperties()
    sub_resource_relationship: S1AppFindingToAccountRel = S1AppFindingToAccountRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            S1AppFindingToApplicationVersionRel(),
            S1AppFindingToAgentRel(),
            S1AppFindingToCVERel(),
        ]
    )
