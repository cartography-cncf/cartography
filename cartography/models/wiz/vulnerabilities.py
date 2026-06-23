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
class WizVulnerabilityFindingNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    cve_id: PropertyRef = PropertyRef("cve_id", extra_index=True)
    cve_description: PropertyRef = PropertyRef("cve_description")
    cvss_severity: PropertyRef = PropertyRef("cvss_severity", extra_index=True)
    score: PropertyRef = PropertyRef("score")
    exploitability_score: PropertyRef = PropertyRef("exploitability_score")
    impact_score: PropertyRef = PropertyRef("impact_score")
    has_exploit: PropertyRef = PropertyRef("has_exploit")
    has_cisa_kev_exploit: PropertyRef = PropertyRef("has_cisa_kev_exploit")
    status: PropertyRef = PropertyRef("status", extra_index=True)
    vendor_severity: PropertyRef = PropertyRef("vendor_severity", extra_index=True)
    first_detected_at: PropertyRef = PropertyRef("first_detected_at")
    last_detected_at: PropertyRef = PropertyRef("last_detected_at")
    resolved_at: PropertyRef = PropertyRef("resolved_at")
    description: PropertyRef = PropertyRef("description")
    remediation: PropertyRef = PropertyRef("remediation")
    detailed_name: PropertyRef = PropertyRef("detailed_name")
    version: PropertyRef = PropertyRef("version")
    fixed_version: PropertyRef = PropertyRef("fixed_version")
    detection_method: PropertyRef = PropertyRef("detection_method")
    link: PropertyRef = PropertyRef("link")
    portal_url: PropertyRef = PropertyRef("portal_url")
    location_path: PropertyRef = PropertyRef("location_path")
    resolution_reason: PropertyRef = PropertyRef("resolution_reason")
    resource_id: PropertyRef = PropertyRef("resource_id", extra_index=True)
    resource_name: PropertyRef = PropertyRef("resource_name")
    resource_type: PropertyRef = PropertyRef("resource_type", extra_index=True)
    resource_region: PropertyRef = PropertyRef("resource_region")
    resource_cloud_platform: PropertyRef = PropertyRef("resource_cloud_platform")
    resource_external_id: PropertyRef = PropertyRef(
        "resource_external_id",
        extra_index=True,
    )
    resource_status: PropertyRef = PropertyRef("resource_status")
    subscription_external_id: PropertyRef = PropertyRef(
        "subscription_external_id",
        extra_index=True,
    )
    subscription_name: PropertyRef = PropertyRef("subscription_name")
    project_ids: PropertyRef = PropertyRef("project_ids", extra_index=True)
    project_names: PropertyRef = PropertyRef("project_names", extra_index=True)


@dataclass(frozen=True)
class WizVulnerabilityFindingToTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# (:WizTenant)-[:RESOURCE]->(:WizVulnerabilityFinding)
@dataclass(frozen=True)
class WizVulnerabilityFindingToTenantRel(CartographyRelSchema):
    target_node_label: str = "WizTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WIZ_TENANT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: WizVulnerabilityFindingToTenantRelProperties = (
        WizVulnerabilityFindingToTenantRelProperties()
    )


@dataclass(frozen=True)
class WizVulnerabilityFindingToResourceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# (:WizVulnerabilityFinding)-[:AFFECTS]->(:WizResource)
@dataclass(frozen=True)
class WizVulnerabilityFindingToResourceRel(CartographyRelSchema):
    target_node_label: str = "WizResource"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("resource_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "AFFECTS"
    properties: WizVulnerabilityFindingToResourceRelProperties = (
        WizVulnerabilityFindingToResourceRelProperties()
    )


@dataclass(frozen=True)
class WizVulnerabilityFindingToCVERelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# (:WizVulnerabilityFinding)-[:LINKED_TO]->(:CVE)
@dataclass(frozen=True)
class WizVulnerabilityFindingToCVERel(CartographyRelSchema):
    target_node_label: str = "CVE"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("cve_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "LINKED_TO"
    properties: WizVulnerabilityFindingToCVERelProperties = (
        WizVulnerabilityFindingToCVERelProperties()
    )


@dataclass(frozen=True)
class WizVulnerabilityFindingSchema(CartographyNodeSchema):
    label: str = "WizVulnerabilityFinding"
    properties: WizVulnerabilityFindingNodeProperties = (
        WizVulnerabilityFindingNodeProperties()
    )
    sub_resource_relationship: WizVulnerabilityFindingToTenantRel = (
        WizVulnerabilityFindingToTenantRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            WizVulnerabilityFindingToResourceRel(),
            WizVulnerabilityFindingToCVERel(),
        ],
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Risk"])
