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
    id: PropertyRef = PropertyRef(
        "id",
        description="Unique Spotlight vulnerability ID.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last Cartography update.",
    )
    aid: PropertyRef = PropertyRef(
        "aid",
        description="Agent ID of the host on which the vulnerability was detected.",
    )
    cid: PropertyRef = PropertyRef(
        "cid",
        description="CrowdStrike customer ID.",
    )
    status: PropertyRef = PropertyRef(
        "status",
        description="Current Spotlight vulnerability status.",
    )
    created_timestamp: PropertyRef = PropertyRef(
        "created_timestamp",
        description="Timestamp when Spotlight created the vulnerability record.",
    )
    closed_timestamp: PropertyRef = PropertyRef(
        "closed_timestamp",
        description="Timestamp when the vulnerability was closed.",
    )
    updated_timestamp: PropertyRef = PropertyRef(
        "updated_timestamp",
        description="Timestamp when Spotlight last updated the vulnerability.",
    )
    cve_id: PropertyRef = PropertyRef(
        "cve_id",
        extra_index=True,
        description="CVE identifier associated with the vulnerability.",
    )
    host_info_local_ip: PropertyRef = PropertyRef(
        "host_info_local_ip",
        extra_index=True,
        description="Local IP address of the affected host.",
    )
    remediation_ids: PropertyRef = PropertyRef(
        "remediation_ids",
        description="Identifiers of available remediation actions.",
    )
    app_product_name_version: PropertyRef = PropertyRef(
        "app_product_name_version",
        description="Affected application product name and version.",
    )


@dataclass(frozen=True)
class SpotlightVulnerabilityRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last Cartography update.",
    )


# (:CrowdstrikeTenant)-[:RESOURCE]->(:SpotlightVulnerability)
@dataclass(frozen=True)
class SpotlightVulnerabilityToCrowdstrikeTenantRel(CartographyRelSchema):
    """The CrowdStrike tenant contains this vulnerability as a managed resource."""

    target_node_label: str = "CrowdstrikeTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("CID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SpotlightVulnerabilityRelProperties = (
        SpotlightVulnerabilityRelProperties()
    )


# (:CrowdstrikeHost)-[:HAS_VULNERABILITY]->(:SpotlightVulnerability)
@dataclass(frozen=True)
class SpotlightVulnerabilityToCrowdstrikeHostRel(CartographyRelSchema):
    """Links a CrowdStrike host to a vulnerability detected on that host."""

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
    """A vulnerability detection reported by CrowdStrike Spotlight."""

    label: str = "SpotlightVulnerability"
    properties: SpotlightVulnerabilityNodeProperties = (
        SpotlightVulnerabilityNodeProperties()
    )
    sub_resource_relationship: SpotlightVulnerabilityToCrowdstrikeTenantRel = (
        SpotlightVulnerabilityToCrowdstrikeTenantRel()
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
    id: PropertyRef = PropertyRef("id", description="CVE identifier.")
    cve_id: PropertyRef = PropertyRef(
        "id",
        extra_index=True,
        description="CVE identifier indexed for cross-module correlation.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last Cartography update.",
    )
    base_score: PropertyRef = PropertyRef(
        "base_score",
        description="CVSS base score for the CVE.",
    )
    base_severity: PropertyRef = PropertyRef(
        "severity",
        description="Severity assigned to the CVE.",
    )
    exploitability_score: PropertyRef = PropertyRef(
        "exploit_status",
        description="Numeric score describing known exploit availability.",
    )


# (:SpotlightVulnerability)-[:HAS_CVE]->(:CVE)
@dataclass(frozen=True)
class CrowdstrikeCVEToSpotlightVulnerabilityRel(CartographyRelSchema):
    """Links a Spotlight vulnerability detection to its CVE."""

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
    """A CVE definition derived from CrowdStrike Spotlight data."""

    label: str = "CrowdstrikeFinding"
    scoped_cleanup: bool = False
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["CVE"])
    properties: CrowdstrikeCVENodeProperties = CrowdstrikeCVENodeProperties()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            CrowdstrikeCVEToSpotlightVulnerabilityRel(),
        ]
    )
