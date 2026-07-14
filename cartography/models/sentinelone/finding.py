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
    id: PropertyRef = PropertyRef(
        "id",
        extra_index=True,
        description="SentinelOne application vulnerability finding ID.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated.",
    )
    cve_id: PropertyRef = PropertyRef(
        "cve_id",
        extra_index=True,
        description="CVE identifier associated with the finding.",
    )
    severity: PropertyRef = PropertyRef(
        "severity",
        description="Finding severity.",
    )
    days_detected: PropertyRef = PropertyRef(
        "days_detected",
        description="Number of days since the vulnerability was detected.",
    )
    detection_date: PropertyRef = PropertyRef(
        "detection_date",
        description="Vulnerability detection timestamp.",
    )
    last_scan_date: PropertyRef = PropertyRef(
        "last_scan_date",
        description="Timestamp of the latest vulnerability scan.",
    )
    last_scan_result: PropertyRef = PropertyRef(
        "last_scan_result",
        description="Result of the latest vulnerability scan.",
    )
    status: PropertyRef = PropertyRef(
        "status",
        description="Current finding status.",
    )
    mitigation_status: PropertyRef = PropertyRef(
        "mitigation_status",
        description="Current mitigation status.",
    )
    mitigation_status_reason: PropertyRef = PropertyRef(
        "mitigation_status_reason",
        description="Reason for the mitigation status.",
    )
    mitigation_status_changed_by: PropertyRef = PropertyRef(
        "mitigation_status_changed_by",
        description="User who last changed the mitigation status.",
    )
    mitigation_status_change_time: PropertyRef = PropertyRef(
        "mitigation_status_change_time",
        description="Timestamp of the latest mitigation status change.",
    )
    marked_by: PropertyRef = PropertyRef(
        "marked_by",
        description="User who marked the finding.",
    )
    marked_date: PropertyRef = PropertyRef(
        "marked_date",
        description="Timestamp when the finding was marked.",
    )
    mark_type_description: PropertyRef = PropertyRef(
        "mark_type_description",
        description="Description of the mark applied to the finding.",
    )
    reason: PropertyRef = PropertyRef(
        "reason",
        description="Reason recorded for the finding.",
    )
    remediation_level: PropertyRef = PropertyRef(
        "remediation_level",
        description="Required remediation level.",
    )
    risk_score: PropertyRef = PropertyRef(
        "risk_score",
        description="SentinelOne risk score.",
    )
    report_confidence: PropertyRef = PropertyRef(
        "report_confidence",
        description="Confidence level of the finding report.",
    )


@dataclass(frozen=True)
class S1AppFindingToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class S1AppFindingToAccountRel(CartographyRelSchema):
    """Links a SentinelOne account to one of its application findings."""

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
class S1AppFindingToApplicationVersionRel(CartographyRelSchema):
    """Links a finding to the application version it affects."""

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
class S1AppFindingToAgentRel(CartographyRelSchema):
    """Links a finding to the endpoint agent it affects."""

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
class S1AppFindingToCVERel(CartographyRelSchema):
    """Links a SentinelOne finding to its generic CVE definition."""

    target_node_label: str = "CVE"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("cve_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "LINKED_TO"
    properties: S1AppFindingToCVERelProperties = S1AppFindingToCVERelProperties()


@dataclass(frozen=True)
class S1AppFindingSchema(CartographyNodeSchema):
    """A vulnerability finding for software on a SentinelOne endpoint."""

    label: str = "S1AppFinding"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["S1Finding", "Risk", "CVE"])
    properties: S1AppFindingNodeProperties = S1AppFindingNodeProperties()
    sub_resource_relationship: S1AppFindingToAccountRel = S1AppFindingToAccountRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            S1AppFindingToApplicationVersionRel(),
            S1AppFindingToAgentRel(),
            S1AppFindingToCVERel(),
        ]
    )
