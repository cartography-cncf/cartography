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
class S1CVENodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", extra_index=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)

    # CVE specific
    cve_id: PropertyRef = PropertyRef("cve_id", extra_index=True)
    base_score: PropertyRef = PropertyRef("base_score")
    cvss_version: PropertyRef = PropertyRef("cvss_version")
    published_date: PropertyRef = PropertyRef("published_date")
    severity: PropertyRef = PropertyRef("severity")
    nvd_base_score: PropertyRef = PropertyRef("nvd_base_score")
    nvd_cvss_version: PropertyRef = PropertyRef("nvd_cvss_version")
    remediation_level: PropertyRef = PropertyRef("remediation_level")
    exploit_code_maturity: PropertyRef = PropertyRef("exploit_code_maturity")
    risk_score: PropertyRef = PropertyRef("risk_score")
    report_confidence: PropertyRef = PropertyRef("report_confidence")

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
    endpoint_id: PropertyRef = PropertyRef("endpoint_id")
    endpoint_name: PropertyRef = PropertyRef("endpoint_name")
    endpoint_type: PropertyRef = PropertyRef("endpoint_type")
    os_type: PropertyRef = PropertyRef("os_type")


@dataclass(frozen=True)
class S1CVEToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:S1CVE)<-[:RESOURCE]-(:S1Account)
class S1CVEToAccountRel(CartographyRelSchema):
    target_node_label: str = "S1Account"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("S1_ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: S1CVEToAccountRelProperties = S1CVEToAccountRelProperties()


@dataclass(frozen=True)
class S1CVEToApplicationVersionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:S1CVE)-[:AFFECTS]->(:S1ApplicationVersion)
class S1CVEToApplicationVersionRel(CartographyRelSchema):
    target_node_label: str = "S1ApplicationVersion"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("application_version_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "AFFECTS"
    properties: S1CVEToApplicationVersionRelProperties = (
        S1CVEToApplicationVersionRelProperties()
    )


@dataclass(frozen=True)
class S1CVEToAgentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:S1CVE)-[:AFFECTS]->(:S1Agent)
class S1CVEToAgentRel(CartographyRelSchema):
    target_node_label: str = "S1Agent"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("endpoint_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "AFFECTS"
    properties: S1CVEToAgentRelProperties = S1CVEToAgentRelProperties()


@dataclass(frozen=True)
class S1CVESchema(CartographyNodeSchema):
    label: str = "S1CVE"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["S1Finding", "Risk", "CVE"])
    properties: S1CVENodeProperties = S1CVENodeProperties()
    sub_resource_relationship: S1CVEToAccountRel = S1CVEToAccountRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            S1CVEToApplicationVersionRel(),
            S1CVEToAgentRel(),
        ]
    )
