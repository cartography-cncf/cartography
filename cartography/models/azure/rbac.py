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
from cartography.models.ontology.labels import PERMISSION_ROLE


# Node Properties - Role Assignment as a Node
@dataclass(frozen=True)
class AzureRoleAssignmentProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Azure Resource Manager ID of the role assignment.",
    )
    name: PropertyRef = PropertyRef(
        "name",
        description="Name of the role assignment.",
    )
    type: PropertyRef = PropertyRef(
        "type",
        description="Azure resource type of the role assignment.",
    )
    principal_id: PropertyRef = PropertyRef(
        "principalId",
        description="Microsoft Entra object ID of the assigned principal.",
    )
    principal_type: PropertyRef = PropertyRef(
        "principalType",
        description="Type of the assigned principal.",
    )
    role_definition_id: PropertyRef = PropertyRef(
        "roleDefinitionId",
        description="Azure Resource Manager ID of the assigned role definition.",
    )
    scope: PropertyRef = PropertyRef(
        "scope",
        extra_index=True,
        description="Azure resource scope where the role assignment applies.",
    )
    scope_type: PropertyRef = PropertyRef(
        "scopeType",
        description="Type of Azure resource scope where the assignment applies.",
    )
    created_on: PropertyRef = PropertyRef(
        "createdOn",
        description="Timestamp when the role assignment was created.",
    )
    updated_on: PropertyRef = PropertyRef(
        "updatedOn",
        description="Timestamp when the role assignment was last updated.",
    )
    created_by: PropertyRef = PropertyRef(
        "createdBy",
        description="Microsoft Entra object ID that created the role assignment.",
    )
    updated_by: PropertyRef = PropertyRef(
        "updatedBy",
        description="Microsoft Entra object ID that last updated the role assignment.",
    )
    condition: PropertyRef = PropertyRef(
        "condition",
        description="Optional condition that limits the role assignment, encoded as JSON.",
    )
    description: PropertyRef = PropertyRef(
        "description",
        description="Description of the role assignment.",
    )
    delegated_managed_identity_resource_id: PropertyRef = PropertyRef(
        "delegatedManagedIdentityResourceId",
        description="Resource ID of the delegated managed identity associated with the assignment.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    subscription_id: PropertyRef = PropertyRef(
        "subscription_id",
        description="Azure subscription ID associated with the role assignment.",
    )
    management_group_id: PropertyRef = PropertyRef(
        "management_group_id",
        description="Azure Resource Manager ID of the associated management group.",
    )


@dataclass(frozen=True)
class AzureRoleDefinitionProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Azure Resource Manager ID of the role definition.",
    )
    name: PropertyRef = PropertyRef(
        "name",
        description="Name of the role definition resource.",
    )
    type: PropertyRef = PropertyRef(
        "type",
        description="Azure resource type of the role definition.",
    )
    role_name: PropertyRef = PropertyRef(
        "roleName",
        description="Display name of the Azure role.",
    )
    description: PropertyRef = PropertyRef(
        "description",
        description="Description of the Azure role.",
    )
    assignable_scopes: PropertyRef = PropertyRef(
        "assignableScopes",
        description="Azure resource scopes where the role can be assigned.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    subscription_id: PropertyRef = PropertyRef(
        "subscription_id",
        description="Azure subscription ID associated with the role definition.",
    )


@dataclass(frozen=True)
class AzureUnscopedRoleDefinitionProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Azure Resource Manager ID of the role definition.",
    )
    name: PropertyRef = PropertyRef(
        "name",
        description="Name of the role definition resource.",
    )
    type: PropertyRef = PropertyRef(
        "type",
        description="Azure resource type of the role definition.",
    )
    role_name: PropertyRef = PropertyRef(
        "roleName",
        description="Display name of the Azure role.",
    )
    description: PropertyRef = PropertyRef(
        "description",
        description="Description of the Azure role.",
    )
    assignable_scopes: PropertyRef = PropertyRef(
        "assignableScopes",
        description="Azure resource scopes where the role can be assigned.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzurePermissionsProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Identifier of the permission set within its role definition.",
    )
    actions: PropertyRef = PropertyRef(
        "actions",
        description="Control plane operations granted by the permission set.",
    )
    not_actions: PropertyRef = PropertyRef(
        "not_actions",
        description="Control plane operations excluded from the granted actions.",
    )
    data_actions: PropertyRef = PropertyRef(
        "data_actions",
        description="Data plane operations granted by the permission set.",
    )
    not_data_actions: PropertyRef = PropertyRef(
        "not_data_actions",
        description="Data plane operations excluded from the granted data actions.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    subscription_id: PropertyRef = PropertyRef(
        "subscription_id",
        description="Azure subscription ID associated with the permission set.",
    )


@dataclass(frozen=True)
class AzureUnscopedPermissionsProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Identifier of the permission set within its role definition.",
    )
    actions: PropertyRef = PropertyRef(
        "actions",
        description="Control plane operations granted by the permission set.",
    )
    not_actions: PropertyRef = PropertyRef(
        "not_actions",
        description="Control plane operations excluded from the granted actions.",
    )
    data_actions: PropertyRef = PropertyRef(
        "data_actions",
        description="Data plane operations granted by the permission set.",
    )
    not_data_actions: PropertyRef = PropertyRef(
        "not_data_actions",
        description="Data plane operations excluded from the granted data actions.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# Relationship Properties for standard relationships
@dataclass(frozen=True)
class AzureRoleAssignmentToSubscriptionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureRoleAssignmentToManagementGroupRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureRoleDefinitionToSubscriptionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureRoleAssignmentToEntraUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureRoleAssignmentToEntraGroupRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureRoleAssignmentToEntraServicePrincipalRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureRoleAssignmentToRoleDefinitionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureRoleDefinitionToPermissionsRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzurePermissionsToSubscriptionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# Standard Relationships
@dataclass(frozen=True)
class AzureRoleAssignmentToSubscriptionRel(CartographyRelSchema):
    """An Azure subscription contains the role assignment as a resource."""

    target_node_label: str = "AzureSubscription"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("AZURE_SUBSCRIPTION_ID", set_in_kwargs=True),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AzureRoleAssignmentToSubscriptionRelProperties = (
        AzureRoleAssignmentToSubscriptionRelProperties()
    )


@dataclass(frozen=True)
class AzureRoleAssignmentToManagementGroupRel(CartographyRelSchema):
    """An Azure management group contains the role assignment as a resource."""

    target_node_label: str = "AzureManagementGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("AZURE_MANAGEMENT_GROUP_ID", set_in_kwargs=True),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AzureRoleAssignmentToManagementGroupRelProperties = (
        AzureRoleAssignmentToManagementGroupRelProperties()
    )


@dataclass(frozen=True)
class AzureRoleDefinitionToSubscriptionRel(CartographyRelSchema):
    """An Azure subscription contains the role definition as a resource."""

    target_node_label: str = "AzureSubscription"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("AZURE_SUBSCRIPTION_ID", set_in_kwargs=True),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AzureRoleDefinitionToSubscriptionRelProperties = (
        AzureRoleDefinitionToSubscriptionRelProperties()
    )


@dataclass(frozen=True)
class AzureRoleAssignmentToRoleDefinitionRel(CartographyRelSchema):
    """An Azure role assignment grants a role definition."""

    target_node_label: str = "AzureRoleDefinition"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("roleDefinitionId"),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ROLE_ASSIGNED"
    properties: AzureRoleAssignmentToRoleDefinitionRelProperties = (
        AzureRoleAssignmentToRoleDefinitionRelProperties()
    )


# Relationships from Azure Role Assignment to Entra Principals
@dataclass(frozen=True)
class AzureRoleAssignmentToEntraUserRel(CartographyRelSchema):
    """A Microsoft Entra user has the Azure role assignment."""

    target_node_label: str = "EntraUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("principalId"),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_ROLE_ASSIGNMENT"
    properties: AzureRoleAssignmentToEntraUserRelProperties = (
        AzureRoleAssignmentToEntraUserRelProperties()
    )


@dataclass(frozen=True)
class AzureRoleAssignmentToEntraGroupRel(CartographyRelSchema):
    """A Microsoft Entra group has the Azure role assignment."""

    target_node_label: str = "EntraGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("principalId"),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_ROLE_ASSIGNMENT"
    properties: AzureRoleAssignmentToEntraGroupRelProperties = (
        AzureRoleAssignmentToEntraGroupRelProperties()
    )


@dataclass(frozen=True)
class AzureRoleAssignmentToEntraServicePrincipalRel(CartographyRelSchema):
    """A Microsoft Entra service principal has the Azure role assignment."""

    target_node_label: str = "EntraServicePrincipal"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("principalId"),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_ROLE_ASSIGNMENT"
    properties: AzureRoleAssignmentToEntraServicePrincipalRelProperties = (
        AzureRoleAssignmentToEntraServicePrincipalRelProperties()
    )


@dataclass(frozen=True)
class AzureRoleDefinitionToPermissionsRel(CartographyRelSchema):
    """An Azure role definition contains one or more permission sets."""

    target_node_label: str = "AzurePermissions"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("permission_ids", one_to_many=True),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_PERMISSIONS"
    properties: AzureRoleDefinitionToPermissionsRelProperties = (
        AzureRoleDefinitionToPermissionsRelProperties()
    )


@dataclass(frozen=True)
class AzurePermissionsToSubscriptionRel(CartographyRelSchema):
    """An Azure subscription contains the permission set as a resource."""

    target_node_label: str = "AzureSubscription"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("AZURE_SUBSCRIPTION_ID", set_in_kwargs=True),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AzurePermissionsToSubscriptionRelProperties = (
        AzurePermissionsToSubscriptionRelProperties()
    )


# Node Schemas
@dataclass(frozen=True)
class AzureRoleAssignmentSchema(CartographyNodeSchema):
    """An Azure role assignment that grants a role to a principal at a scope."""

    label: str = "AzureRoleAssignment"
    properties: AzureRoleAssignmentProperties = AzureRoleAssignmentProperties()
    sub_resource_relationship: AzureRoleAssignmentToSubscriptionRel = (
        AzureRoleAssignmentToSubscriptionRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AzureRoleAssignmentToRoleDefinitionRel(),
            AzureRoleAssignmentToEntraUserRel(),
            AzureRoleAssignmentToEntraGroupRel(),
            AzureRoleAssignmentToEntraServicePrincipalRel(),
        ]
    )


@dataclass(frozen=True)
class AzureManagementGroupRoleAssignmentSchema(CartographyNodeSchema):
    """An Azure role assignment that grants a role to a principal at a scope."""

    label: str = "AzureRoleAssignment"
    properties: AzureRoleAssignmentProperties = AzureRoleAssignmentProperties()
    sub_resource_relationship: AzureRoleAssignmentToManagementGroupRel = (
        AzureRoleAssignmentToManagementGroupRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AzureRoleAssignmentToRoleDefinitionRel(),
            AzureRoleAssignmentToEntraUserRel(),
            AzureRoleAssignmentToEntraGroupRel(),
            AzureRoleAssignmentToEntraServicePrincipalRel(),
        ]
    )


@dataclass(frozen=True)
class AzureRoleDefinitionSchema(CartographyNodeSchema):
    """An Azure role definition that specifies assignable permissions."""

    label: str = "AzureRoleDefinition"
    properties: AzureRoleDefinitionProperties = AzureRoleDefinitionProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([PERMISSION_ROLE])
    sub_resource_relationship: AzureRoleDefinitionToSubscriptionRel = (
        AzureRoleDefinitionToSubscriptionRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AzureRoleDefinitionToPermissionsRel(),
        ]
    )


@dataclass(frozen=True)
class AzureUnscopedRoleDefinitionSchema(CartographyNodeSchema):
    """An Azure role definition that specifies assignable permissions."""

    label: str = "AzureRoleDefinition"
    properties: AzureUnscopedRoleDefinitionProperties = (
        AzureUnscopedRoleDefinitionProperties()
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([PERMISSION_ROLE])
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AzureRoleDefinitionToPermissionsRel(),
        ]
    )


@dataclass(frozen=True)
class AzurePermissionsSchema(CartographyNodeSchema):
    """A set of control plane and data plane permissions in an Azure role."""

    label: str = "AzurePermissions"
    properties: AzurePermissionsProperties = AzurePermissionsProperties()
    sub_resource_relationship: AzurePermissionsToSubscriptionRel = (
        AzurePermissionsToSubscriptionRel()
    )


@dataclass(frozen=True)
class AzureUnscopedPermissionsSchema(CartographyNodeSchema):
    """A set of control plane and data plane permissions in an Azure role."""

    label: str = "AzurePermissions"
    properties: AzureUnscopedPermissionsProperties = (
        AzureUnscopedPermissionsProperties()
    )
