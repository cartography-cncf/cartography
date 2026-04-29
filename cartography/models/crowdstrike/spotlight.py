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

# =============================================================================
# SpotlightVulnerability
# =============================================================================


@dataclass(frozen=True)
class SpotlightVulnerabilityNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    aid: PropertyRef = PropertyRef("aid")
    cid: PropertyRef = PropertyRef("cid")
    status: PropertyRef = PropertyRef("status")
    created_timestamp: PropertyRef = PropertyRef("created_timestamp")
    closed_timestamp: PropertyRef = PropertyRef("closed_timestamp")
    updated_timestamp: PropertyRef = PropertyRef("updated_timestamp")
    cve_id: PropertyRef = PropertyRef("cve_id", extra_index=True)
    host_info_local_ip: PropertyRef = PropertyRef(
        "host_info_local_ip", extra_index=True
    )
    remediation_ids: PropertyRef = PropertyRef("remediation_ids")
    app_product_name_version: PropertyRef = PropertyRef("app_product_name_version")


@dataclass(frozen=True)
class SpotlightVulnerabilityRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# (:CrowdstrikeHost)-[:HAS_VULNERABILITY]->(:SpotlightVulnerability)
@dataclass(frozen=True)
class SpotlightVulnerabilityToCrowdstrikeHostRel(CartographyRelSchema):
    target_node_label: str = "CrowdstrikeHost"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("aid")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_VULNERABILITY"
    properties: SpotlightVulnerabilityRelProperties = (
        SpotlightVulnerabilityRelProperties()
    )


@dataclass(frozen=True)
class SpotlightVulnerabilitySchema(CartographyNodeSchema):
    label: str = "SpotlightVulnerability"
    properties: SpotlightVulnerabilityNodeProperties = (
        SpotlightVulnerabilityNodeProperties()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            SpotlightVulnerabilityToCrowdstrikeHostRel(),
        ]
    )


# =============================================================================
# CVE (CrowdstrikeFinding)
# =============================================================================


@dataclass(frozen=True)
class CrowdstrikeCVENodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    cve_id: PropertyRef = PropertyRef("id", extra_index=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    base_score: PropertyRef = PropertyRef("base_score")
    base_severity: PropertyRef = PropertyRef("severity")
    exploitability_score: PropertyRef = PropertyRef("exploit_status")


# (:SpotlightVulnerability)-[:HAS_CVE]->(:CVE)
@dataclass(frozen=True)
class CrowdstrikeCVEToSpotlightVulnerabilityRel(CartographyRelSchema):
    target_node_label: str = "SpotlightVulnerability"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("vuln_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_CVE"
    properties: SpotlightVulnerabilityRelProperties = (
        SpotlightVulnerabilityRelProperties()
    )


@dataclass(frozen=True)
class CrowdstrikeCVESchema(CartographyNodeSchema):
    label: str = "CrowdstrikeFinding"
    scoped_cleanup: bool = False
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["CVE"])
    properties: CrowdstrikeCVENodeProperties = CrowdstrikeCVENodeProperties()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            CrowdstrikeCVEToSpotlightVulnerabilityRel(),
        ]
    )
