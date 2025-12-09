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
    base_score: PropertyRef = PropertyRef("base_score")
    cve_id: PropertyRef = PropertyRef("cve_id", extra_index=True)
    cvss_version: PropertyRef = PropertyRef("cvss_version")
    published_date: PropertyRef = PropertyRef("published_date")
    severity: PropertyRef = PropertyRef("severity")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class S1CVEToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:S1CVE)<-[:RISK]-(:S1Account)
class S1CVEToAccount(CartographyRelSchema):
    target_node_label: str = "S1Account"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("S1_ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RISK"
    properties: S1CVEToAccountRelProperties = S1CVEToAccountRelProperties()


@dataclass(frozen=True)
class S1AffectsRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    days_detected: PropertyRef = PropertyRef("days_detected")
    detection_date: PropertyRef = PropertyRef("detection_date")
    last_scan_date: PropertyRef = PropertyRef("last_scan_date")
    last_scan_result: PropertyRef = PropertyRef("last_scan_result")
    status: PropertyRef = PropertyRef("status")


@dataclass(frozen=True)
# (:S1CVE)-[:AFFECTS]->(:S1ApplicationVersion)
class S1CVEAffectsApplicationVersion(CartographyRelSchema):
    target_node_label: str = "S1ApplicationVersion"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("application_version_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "AFFECTS"
    properties: S1AffectsRelProperties = S1AffectsRelProperties()


@dataclass(frozen=True)
class S1CVESchema(CartographyNodeSchema):
    label: str = "S1CVE"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Risk", "CVE"])
    properties: S1CVENodeProperties = S1CVENodeProperties()
    sub_resource_relationship: S1CVEToAccount = S1CVEToAccount()
    other_relationships: OtherRelationships = OtherRelationships(
        [S1CVEAffectsApplicationVersion()]
    )
