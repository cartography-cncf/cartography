from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher
from cartography.models.ontology.labels import SECURITY_ISSUE


@dataclass(frozen=True)
class WizIssueNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Wiz issue ID.")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp when this Wiz issue was last seen.",
    )
    name: PropertyRef = PropertyRef(
        "name",
        extra_index=True,
        description="Wiz issue name.",
    )
    status: PropertyRef = PropertyRef(
        "status",
        extra_index=True,
        description="Wiz issue status.",
    )
    severity: PropertyRef = PropertyRef(
        "severity",
        extra_index=True,
        description="Wiz issue severity.",
    )
    issue_type: PropertyRef = PropertyRef(
        "issue_type",
        extra_index=True,
        description="Wiz issue type.",
    )
    created_at: PropertyRef = PropertyRef(
        "created_at",
        description="Timestamp when Wiz created the issue.",
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at",
        description="Timestamp when Wiz last updated the issue.",
    )
    due_at: PropertyRef = PropertyRef(
        "due_at",
        description="Wiz issue due timestamp.",
    )
    resolved_at: PropertyRef = PropertyRef(
        "resolved_at",
        description="Timestamp when Wiz resolved the issue.",
    )
    status_changed_at: PropertyRef = PropertyRef(
        "status_changed_at",
        description="Timestamp when the Wiz issue status last changed.",
    )
    control_id: PropertyRef = PropertyRef(
        "control_id",
        extra_index=True,
        description="Wiz control ID associated with the issue.",
    )
    control_name: PropertyRef = PropertyRef(
        "control_name",
        description="Wiz control name associated with the issue.",
    )
    control_description: PropertyRef = PropertyRef(
        "control_description",
        description="Wiz control description associated with the issue.",
    )
    resolution_recommendation: PropertyRef = PropertyRef(
        "resolution_recommendation",
        description="Wiz remediation guidance for the issue.",
    )
    source_rule_id: PropertyRef = PropertyRef(
        "source_rule_id",
        extra_index=True,
        description="Wiz source rule ID for the issue.",
    )
    source_rule_name: PropertyRef = PropertyRef(
        "source_rule_name",
        description="Wiz source rule name for the issue.",
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
    resource_cloud_platform: PropertyRef = PropertyRef(
        "resource_cloud_platform",
        description="Cloud platform of the affected resource.",
    )
    resource_external_id: PropertyRef = PropertyRef(
        "resource_external_id",
        extra_index=True,
        description="Provider-native ID of the affected resource.",
    )
    project_ids: PropertyRef = PropertyRef(
        "project_ids",
        extra_index=True,
        description="Wiz project IDs associated with the issue.",
    )
    project_names: PropertyRef = PropertyRef(
        "project_names",
        description="Wiz project names associated with the issue.",
    )
    service_ticket_urls: PropertyRef = PropertyRef(
        "service_ticket_urls",
        description="Service ticket URLs associated with the issue.",
    )


@dataclass(frozen=True)
class WizIssueToTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# (:WizTenant)-[:RESOURCE]->(:WizIssue)
@dataclass(frozen=True)
class WizIssueToTenantRel(CartographyRelSchema):
    target_node_label: str = "WizTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WIZ_TENANT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: WizIssueToTenantRelProperties = WizIssueToTenantRelProperties()


@dataclass(frozen=True)
class WizIssueSchema(CartographyNodeSchema):
    label: str = "WizIssue"
    properties: WizIssueNodeProperties = WizIssueNodeProperties()
    sub_resource_relationship: WizIssueToTenantRel = WizIssueToTenantRel()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([SECURITY_ISSUE])
