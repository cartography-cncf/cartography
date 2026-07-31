from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class AzureManagementGroupProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Azure Resource Manager ID of the management group.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name",
        description="Name of the management group.",
    )
    displayname: PropertyRef = PropertyRef(
        "displayName",
        description="Display name of the management group.",
    )
    tenantid: PropertyRef = PropertyRef(
        "tenantId",
        description="Microsoft tenant ID associated with the management group.",
    )
    type: PropertyRef = PropertyRef(
        "type",
        description="Azure resource type of the management group.",
    )
    updatedby: PropertyRef = PropertyRef(
        "updatedBy",
        description="Identifier of the principal that last updated the management group.",
    )
    updatedtime: PropertyRef = PropertyRef(
        "updatedTime",
        description="Timestamp when the management group was last updated.",
    )
    version: PropertyRef = PropertyRef(
        "version",
        description="Version number of the management group record.",
    )
    parent_tenant_id: PropertyRef = PropertyRef(
        "parent_tenant_id",
        description="Microsoft tenant ID when the tenant is the direct parent.",
    )
    parent_management_group_id: PropertyRef = PropertyRef(
        "parent_management_group_id",
        description="Azure Resource Manager ID of the parent management group.",
    )


@dataclass(frozen=True)
class AzureManagementGroupToTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureManagementGroupToTenantRel(CartographyRelSchema):
    """An Azure tenant contains the management group as a resource."""

    target_node_label: str = "AzureTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TENANT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AzureManagementGroupToTenantRelProperties = (
        AzureManagementGroupToTenantRelProperties()
    )


@dataclass(frozen=True)
class AzureManagementGroupToParentTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureManagementGroupToParentTenantRel(CartographyRelSchema):
    """A root Azure management group has the tenant as its parent."""

    target_node_label: str = "AzureTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("parent_tenant_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "PARENT"
    properties: AzureManagementGroupToParentTenantRelProperties = (
        AzureManagementGroupToParentTenantRelProperties()
    )


@dataclass(frozen=True)
class AzureManagementGroupToParentManagementGroupRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureManagementGroupToParentManagementGroupRel(CartographyRelSchema):
    """An Azure management group has another management group as its parent."""

    target_node_label: str = "AzureManagementGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("parent_management_group_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "PARENT"
    properties: AzureManagementGroupToParentManagementGroupRelProperties = (
        AzureManagementGroupToParentManagementGroupRelProperties()
    )


class AzureManagementGroupSchema(CartographyNodeSchema):
    """An Azure management group used to organize subscriptions and resources."""

    label: str = "AzureManagementGroup"
    properties: AzureManagementGroupProperties = AzureManagementGroupProperties()
    sub_resource_relationship: AzureManagementGroupToTenantRel = (
        AzureManagementGroupToTenantRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AzureManagementGroupToParentTenantRel(),
            AzureManagementGroupToParentManagementGroupRel(),
        ]
    )
