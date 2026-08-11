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
    id: PropertyRef = PropertyRef("id", description="Wiz finding ID.")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp when this Wiz finding was last seen.",
    )
    finding_type: PropertyRef = PropertyRef(
        "finding_type",
        extra_index=True,
        description="Wiz finding family.",
    )
    name: PropertyRef = PropertyRef(
        "name",
        extra_index=True,
        description="Wiz finding name.",
    )
    status: PropertyRef = PropertyRef(
        "status",
        extra_index=True,
        description="Wiz finding status.",
    )
    severity: PropertyRef = PropertyRef(
        "severity",
        extra_index=True,
        description="Wiz finding severity.",
    )
    vendor_severity: PropertyRef = PropertyRef(
        "vendor_severity",
        extra_index=True,
        description="Vendor-reported severity for the finding.",
    )
    result: PropertyRef = PropertyRef(
        "result",
        extra_index=True,
        description="Wiz finding result.",
    )
    created_at: PropertyRef = PropertyRef(
        "created_at",
        description="Timestamp when Wiz created the finding.",
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at",
        description="Timestamp when Wiz last updated the finding.",
    )
    first_seen_at: PropertyRef = PropertyRef(
        "first_seen_at",
        description="Timestamp when Wiz first saw the finding.",
    )
    first_detected_at: PropertyRef = PropertyRef(
        "first_detected_at",
        description="Timestamp when Wiz first detected the finding.",
    )
    last_detected_at: PropertyRef = PropertyRef(
        "last_detected_at",
        description="Timestamp when Wiz last detected the finding.",
    )
    resolved_at: PropertyRef = PropertyRef(
        "resolved_at",
        description="Timestamp when Wiz resolved the finding.",
    )
    description: PropertyRef = PropertyRef(
        "description",
        description="Wiz finding description.",
    )
    remediation: PropertyRef = PropertyRef(
        "remediation",
        description="Wiz remediation guidance for the finding.",
    )
    cve_id: PropertyRef = PropertyRef(
        "cve_id",
        extra_index=True,
        description="CVE ID associated with the finding.",
    )
    cve_description: PropertyRef = PropertyRef(
        "cve_description",
        description="CVE description associated with the finding.",
    )
    cvss_severity: PropertyRef = PropertyRef(
        "cvss_severity",
        extra_index=True,
        description="CVSS severity associated with the finding.",
    )
    score: PropertyRef = PropertyRef(
        "score",
        description="CVSS score associated with the finding.",
    )
    exploitability_score: PropertyRef = PropertyRef(
        "exploitability_score",
        description="CVSS exploitability score for the finding.",
    )
    impact_score: PropertyRef = PropertyRef(
        "impact_score",
        description="CVSS impact score for the finding.",
    )
    has_exploit: PropertyRef = PropertyRef(
        "has_exploit",
        description="Whether Wiz reports a known exploit.",
    )
    has_cisa_kev_exploit: PropertyRef = PropertyRef(
        "has_cisa_kev_exploit",
        description="Whether Wiz reports the CVE in the CISA KEV catalog.",
    )
    detailed_name: PropertyRef = PropertyRef(
        "detailed_name",
        description="Detailed vulnerability or finding name from Wiz.",
    )
    version: PropertyRef = PropertyRef(
        "version",
        description="Affected package or component version.",
    )
    fixed_version: PropertyRef = PropertyRef(
        "fixed_version",
        description="Fixed package or component version.",
    )
    detection_method: PropertyRef = PropertyRef(
        "detection_method",
        description="Wiz detection method for the finding.",
    )
    link: PropertyRef = PropertyRef(
        "link",
        description="External reference URL for the finding.",
    )
    portal_url: PropertyRef = PropertyRef(
        "portal_url",
        description="Wiz portal URL for the finding.",
    )
    location_path: PropertyRef = PropertyRef(
        "location_path",
        description="Affected file or runtime path for the finding.",
    )
    resolution_reason: PropertyRef = PropertyRef(
        "resolution_reason",
        description="Reason Wiz marked the finding resolved.",
    )
    target_external_id: PropertyRef = PropertyRef(
        "target_external_id",
        description="External ID of the Wiz finding target.",
    )
    target_object_provider_unique_id: PropertyRef = PropertyRef(
        "target_object_provider_unique_id",
        extra_index=True,
        description="Provider-unique ID of the Wiz finding target.",
    )
    rule_id: PropertyRef = PropertyRef(
        "rule_id",
        extra_index=True,
        description="Wiz rule ID associated with the finding.",
    )
    rule_graph_id: PropertyRef = PropertyRef(
        "rule_graph_id",
        extra_index=True,
        description="Wiz graph rule ID associated with the finding.",
    )
    rule_name: PropertyRef = PropertyRef(
        "rule_name",
        description="Wiz rule name associated with the finding.",
    )
    rule_description: PropertyRef = PropertyRef(
        "rule_description",
        description="Wiz rule description associated with the finding.",
    )
    rule_builtin: PropertyRef = PropertyRef(
        "rule_builtin",
        description="Whether the Wiz rule is built in.",
    )
    rule_as_control: PropertyRef = PropertyRef(
        "rule_as_control",
        description="Whether Wiz treats the rule as a control.",
    )
    resource_id: PropertyRef = PropertyRef(
        "resource_id",
        extra_index=True,
        description="Wiz ID of the affected resource.",
    )
    resource_name: PropertyRef = PropertyRef(
        "resource_name",
        description="Name of the affected Wiz resource.",
    )
    resource_type: PropertyRef = PropertyRef(
        "resource_type",
        extra_index=True,
        description="Wiz type of the affected resource.",
    )
    resource_native_type: PropertyRef = PropertyRef(
        "resource_native_type",
        description="Cloud-native type of the affected resource.",
    )
    resource_region: PropertyRef = PropertyRef(
        "resource_region",
        description="Cloud region of the affected resource.",
    )
    resource_cloud_platform: PropertyRef = PropertyRef(
        "resource_cloud_platform",
        description="Cloud platform of the affected resource.",
    )
    resource_external_id: PropertyRef = PropertyRef(
        "resource_external_id",
        extra_index=True,
        description="Provider-native ID of the affected resource.",
    )
    resource_status: PropertyRef = PropertyRef(
        "resource_status",
        description="Wiz status of the affected resource.",
    )
    subscription_id: PropertyRef = PropertyRef(
        "subscription_id",
        extra_index=True,
        description="Wiz subscription ID for the affected resource.",
    )
    subscription_external_id: PropertyRef = PropertyRef(
        "subscription_external_id",
        extra_index=True,
        description="Provider-native subscription ID for the affected resource.",
    )
    subscription_name: PropertyRef = PropertyRef(
        "subscription_name",
        description="Subscription name for the affected resource.",
    )
    cloud_account_ids: PropertyRef = PropertyRef(
        "cloud_account_ids",
        description="Wiz cloud account IDs associated with the finding.",
    )
    cloud_account_names: PropertyRef = PropertyRef(
        "cloud_account_names",
        description="Wiz cloud account names associated with the finding.",
    )
    cloud_organization_ids: PropertyRef = PropertyRef(
        "cloud_organization_ids",
        description="Wiz cloud organization IDs associated with the finding.",
    )
    cloud_organization_names: PropertyRef = PropertyRef(
        "cloud_organization_names",
        description="Wiz cloud organization names associated with the finding.",
    )
    actor_ids: PropertyRef = PropertyRef(
        "actor_ids",
        description="Wiz actor IDs associated with the finding.",
    )
    actor_names: PropertyRef = PropertyRef(
        "actor_names",
        description="Wiz actor names associated with the finding.",
    )
    origins: PropertyRef = PropertyRef(
        "origins",
        description="Wiz origins associated with the finding.",
    )
    triggering_event_ids: PropertyRef = PropertyRef(
        "triggering_event_ids",
        description="Wiz triggering event IDs for the finding.",
    )
    project_ids: PropertyRef = PropertyRef(
        "project_ids",
        extra_index=True,
        description="Wiz project IDs associated with the finding.",
    )
    project_names: PropertyRef = PropertyRef(
        "project_names",
        description="Wiz project names associated with the finding.",
    )


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
