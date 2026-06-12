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
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name")
    displayname: PropertyRef = PropertyRef("displayName")
    tenantid: PropertyRef = PropertyRef("tenantId")
    type: PropertyRef = PropertyRef("type")
    updatedby: PropertyRef = PropertyRef("updatedBy")
    updatedtime: PropertyRef = PropertyRef("updatedTime")
    version: PropertyRef = PropertyRef("version")
    parent_tenant_id: PropertyRef = PropertyRef("parent_tenant_id")
    parent_management_group_id: PropertyRef = PropertyRef("parent_management_group_id")


@dataclass(frozen=True)
class AzureManagementGroupToTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureManagementGroupToTenantRel(CartographyRelSchema):
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
