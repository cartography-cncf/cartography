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


@dataclass(frozen=True)
class NullifyCSPMFindingNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    rule_id: PropertyRef = PropertyRef("ruleId", extra_index=True)
    title: PropertyRef = PropertyRef("title")
    category: PropertyRef = PropertyRef("category")
    severity: PropertyRef = PropertyRef("severity", extra_index=True)
    # Cloud resource this misconfiguration was found on (no repository linkage).
    account_id: PropertyRef = PropertyRef("accountId", extra_index=True)
    account_name: PropertyRef = PropertyRef("accountName")
    cloud_provider: PropertyRef = PropertyRef("cloudProvider")
    resource_id: PropertyRef = PropertyRef("resourceId", extra_index=True)
    resource_arn: PropertyRef = PropertyRef("resourceArn", extra_index=True)
    resource_name: PropertyRef = PropertyRef("resourceName")
    resource_type: PropertyRef = PropertyRef("resourceType")
    region: PropertyRef = PropertyRef("region")
    priority_label: PropertyRef = PropertyRef("priorityLabel")
    is_resolved: PropertyRef = PropertyRef("isResolved")
    is_false_positive: PropertyRef = PropertyRef("isFalsePositive")
    is_allowlisted: PropertyRef = PropertyRef("isAllowlisted")
    created_at: PropertyRef = PropertyRef("createdAt")
    updated_at: PropertyRef = PropertyRef("updatedAt")


@dataclass(frozen=True)
class NullifyCSPMFindingToTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:NullifyTenant)-[:RESOURCE]->(:NullifyCSPMFinding)
class NullifyCSPMFindingToTenantRel(CartographyRelSchema):
    target_node_label: str = "NullifyTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TENANT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: NullifyCSPMFindingToTenantRelProperties = (
        NullifyCSPMFindingToTenantRelProperties()
    )


@dataclass(frozen=True)
class NullifyCSPMFindingSchema(CartographyNodeSchema):
    label: str = "NullifyCSPMFinding"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["SecurityIssue"])
    properties: NullifyCSPMFindingNodeProperties = NullifyCSPMFindingNodeProperties()
    sub_resource_relationship: NullifyCSPMFindingToTenantRel = (
        NullifyCSPMFindingToTenantRel()
    )
    # TODO: link (:NullifyCSPMFinding)-[:AFFECTS]->(:AWSAccount) via account_id when the
    # cloud-provider modules have run. Deferred to keep the initial module scope tight.
