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
from cartography.models.ontology.labels import TENANT


@dataclass(frozen=True)
class AzureSubscriptionProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "subscriptionId",
        description="Azure subscription ID.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    path: PropertyRef = PropertyRef(
        "id",
        description="Azure Resource Manager path of the subscription.",
    )
    name: PropertyRef = PropertyRef(
        "displayName",
        description="Display name of the subscription.",
    )
    state: PropertyRef = PropertyRef(
        "state",
        description="Current state of the subscription.",
    )
    parent_management_group_id: PropertyRef = PropertyRef(
        "parent_management_group_id",
        description="Azure Resource Manager ID of the parent management group.",
    )


@dataclass(frozen=True)
class AzureSubscriptionToTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureTenant)-[:RESOURCE]->(:AzureSubscription)
class AzureSubscriptionToTenantRel(CartographyRelSchema):
    """An Azure tenant contains the subscription as a resource."""

    target_node_label: str = "AzureTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TENANT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AzureSubscriptionToTenantRelProperties = (
        AzureSubscriptionToTenantRelProperties()
    )


@dataclass(frozen=True)
class AzureSubscriptionToManagementGroupParentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureSubscriptionToManagementGroupParentRel(CartographyRelSchema):
    """An Azure subscription has a parent management group."""

    target_node_label: str = "AzureManagementGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("parent_management_group_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "PARENT"
    properties: AzureSubscriptionToManagementGroupParentRelProperties = (
        AzureSubscriptionToManagementGroupParentRelProperties()
    )


@dataclass(frozen=True)
class AzureSubscriptionSchema(CartographyNodeSchema):
    """An Azure subscription that contains cloud resources."""

    label: str = "AzureSubscription"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([TENANT])
    properties: AzureSubscriptionProperties = AzureSubscriptionProperties()
    sub_resource_relationship: AzureSubscriptionToTenantRel = (
        AzureSubscriptionToTenantRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AzureSubscriptionToManagementGroupParentRel(),
        ]
    )
