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
from cartography.models.extra_labels import RISK


@dataclass(frozen=True)
class WizFindingNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    finding_type: PropertyRef = PropertyRef("finding_type", extra_index=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    status: PropertyRef = PropertyRef("status", extra_index=True)
    severity: PropertyRef = PropertyRef("severity", extra_index=True)
    vendor_severity: PropertyRef = PropertyRef("vendor_severity", extra_index=True)
    result: PropertyRef = PropertyRef("result", extra_index=True)
    created_at: PropertyRef = PropertyRef("created_at")
    updated_at: PropertyRef = PropertyRef("updated_at")
    first_seen_at: PropertyRef = PropertyRef("first_seen_at")
    first_detected_at: PropertyRef = PropertyRef("first_detected_at")
    last_detected_at: PropertyRef = PropertyRef("last_detected_at")
    resolved_at: PropertyRef = PropertyRef("resolved_at")
    description: PropertyRef = PropertyRef("description")
    remediation: PropertyRef = PropertyRef("remediation")
    cve_id: PropertyRef = PropertyRef("cve_id", extra_index=True)
    cve_description: PropertyRef = PropertyRef("cve_description")
    cvss_severity: PropertyRef = PropertyRef("cvss_severity", extra_index=True)
    score: PropertyRef = PropertyRef("score")
    exploitability_score: PropertyRef = PropertyRef("exploitability_score")
    impact_score: PropertyRef = PropertyRef("impact_score")
    has_exploit: PropertyRef = PropertyRef("has_exploit")
    has_cisa_kev_exploit: PropertyRef = PropertyRef("has_cisa_kev_exploit")
    detailed_name: PropertyRef = PropertyRef("detailed_name")
    version: PropertyRef = PropertyRef("version")
    fixed_version: PropertyRef = PropertyRef("fixed_version")
    detection_method: PropertyRef = PropertyRef("detection_method")
    link: PropertyRef = PropertyRef("link")
    portal_url: PropertyRef = PropertyRef("portal_url")
    location_path: PropertyRef = PropertyRef("location_path")
    resolution_reason: PropertyRef = PropertyRef("resolution_reason")
    target_external_id: PropertyRef = PropertyRef("target_external_id")
    target_object_provider_unique_id: PropertyRef = PropertyRef(
        "target_object_provider_unique_id",
        extra_index=True,
    )
    rule_id: PropertyRef = PropertyRef("rule_id", extra_index=True)
    rule_graph_id: PropertyRef = PropertyRef("rule_graph_id", extra_index=True)
    rule_name: PropertyRef = PropertyRef("rule_name")
    rule_description: PropertyRef = PropertyRef("rule_description")
    rule_builtin: PropertyRef = PropertyRef("rule_builtin")
    rule_as_control: PropertyRef = PropertyRef("rule_as_control")
    resource_id: PropertyRef = PropertyRef("resource_id", extra_index=True)
    resource_name: PropertyRef = PropertyRef("resource_name")
    resource_type: PropertyRef = PropertyRef("resource_type", extra_index=True)
    resource_native_type: PropertyRef = PropertyRef("resource_native_type")
    resource_region: PropertyRef = PropertyRef("resource_region")
    resource_cloud_platform: PropertyRef = PropertyRef("resource_cloud_platform")
    resource_external_id: PropertyRef = PropertyRef(
        "resource_external_id",
        extra_index=True,
    )
    resource_status: PropertyRef = PropertyRef("resource_status")
    subscription_id: PropertyRef = PropertyRef("subscription_id", extra_index=True)
    subscription_external_id: PropertyRef = PropertyRef(
        "subscription_external_id",
        extra_index=True,
    )
    subscription_name: PropertyRef = PropertyRef("subscription_name")
    cloud_account_ids: PropertyRef = PropertyRef("cloud_account_ids", extra_index=True)
    cloud_account_names: PropertyRef = PropertyRef(
        "cloud_account_names",
        extra_index=True,
    )
    cloud_organization_ids: PropertyRef = PropertyRef(
        "cloud_organization_ids",
        extra_index=True,
    )
    cloud_organization_names: PropertyRef = PropertyRef("cloud_organization_names")
    actor_ids: PropertyRef = PropertyRef("actor_ids", extra_index=True)
    actor_names: PropertyRef = PropertyRef("actor_names")
    origins: PropertyRef = PropertyRef("origins", extra_index=True)
    triggering_event_ids: PropertyRef = PropertyRef("triggering_event_ids")
    project_ids: PropertyRef = PropertyRef("project_ids", extra_index=True)
    project_names: PropertyRef = PropertyRef("project_names", extra_index=True)


@dataclass(frozen=True)
class WizFindingToTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# (:WizTenant)-[:RESOURCE]->(:WizFinding)
@dataclass(frozen=True)
class WizFindingToTenantRel(CartographyRelSchema):
    target_node_label: str = "WizTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WIZ_TENANT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: WizFindingToTenantRelProperties = WizFindingToTenantRelProperties()


@dataclass(frozen=True)
class WizFindingToCVERelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# (:WizFinding)-[:LINKED_TO]->(:CVE)
@dataclass(frozen=True)
class WizFindingToCVERel(CartographyRelSchema):
    target_node_label: str = "CVE"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("cve_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "LINKED_TO"
    properties: WizFindingToCVERelProperties = WizFindingToCVERelProperties()


@dataclass(frozen=True)
class WizFindingSchema(CartographyNodeSchema):
    label: str = "WizFinding"
    properties: WizFindingNodeProperties = WizFindingNodeProperties()
    sub_resource_relationship: WizFindingToTenantRel = WizFindingToTenantRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            WizFindingToCVERel(),
        ],
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([RISK])
