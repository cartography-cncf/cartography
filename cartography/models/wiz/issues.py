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
class WizIssueNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    status: PropertyRef = PropertyRef("status", extra_index=True)
    severity: PropertyRef = PropertyRef("severity", extra_index=True)
    issue_type: PropertyRef = PropertyRef("issue_type", extra_index=True)
    created_at: PropertyRef = PropertyRef("created_at")
    updated_at: PropertyRef = PropertyRef("updated_at")
    due_at: PropertyRef = PropertyRef("due_at")
    resolved_at: PropertyRef = PropertyRef("resolved_at")
    status_changed_at: PropertyRef = PropertyRef("status_changed_at")
    control_id: PropertyRef = PropertyRef("control_id", extra_index=True)
    control_name: PropertyRef = PropertyRef("control_name")
    control_description: PropertyRef = PropertyRef("control_description")
    resolution_recommendation: PropertyRef = PropertyRef("resolution_recommendation")
    source_rule_id: PropertyRef = PropertyRef("source_rule_id", extra_index=True)
    source_rule_name: PropertyRef = PropertyRef("source_rule_name")
    resource_id: PropertyRef = PropertyRef("resource_id", extra_index=True)
    resource_name: PropertyRef = PropertyRef("resource_name")
    resource_type: PropertyRef = PropertyRef("resource_type", extra_index=True)
    resource_native_type: PropertyRef = PropertyRef("resource_native_type")
    resource_cloud_platform: PropertyRef = PropertyRef("resource_cloud_platform")
    resource_external_id: PropertyRef = PropertyRef(
        "resource_external_id",
        extra_index=True,
    )
    project_ids: PropertyRef = PropertyRef("project_ids", extra_index=True)
    project_names: PropertyRef = PropertyRef("project_names", extra_index=True)
    service_ticket_urls: PropertyRef = PropertyRef("service_ticket_urls")


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
class WizIssueToResourceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# (:WizIssue)-[:AFFECTS]->(:WizResource)
@dataclass(frozen=True)
class WizIssueToResourceRel(CartographyRelSchema):
    target_node_label: str = "WizResource"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("resource_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "AFFECTS"
    properties: WizIssueToResourceRelProperties = WizIssueToResourceRelProperties()


@dataclass(frozen=True)
class WizIssueSchema(CartographyNodeSchema):
    label: str = "WizIssue"
    properties: WizIssueNodeProperties = WizIssueNodeProperties()
    sub_resource_relationship: WizIssueToTenantRel = WizIssueToTenantRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            WizIssueToResourceRel(),
        ],
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Risk"])
