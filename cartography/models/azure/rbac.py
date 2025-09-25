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


# Node Properties - Role Assignment as a Node
@dataclass(frozen=True)
class AzureRoleAssignmentProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name")
    type: PropertyRef = PropertyRef("type")
    principal_id: PropertyRef = PropertyRef("principalId")
    principal_type: PropertyRef = PropertyRef("principalType")
    role_definition_id: PropertyRef = PropertyRef("roleDefinitionId")
    scope: PropertyRef = PropertyRef("scope")
    scope_type: PropertyRef = PropertyRef("scopeType")
    created_on: PropertyRef = PropertyRef("createdOn")
    updated_on: PropertyRef = PropertyRef("updatedOn")
    created_by: PropertyRef = PropertyRef("createdBy")
    updated_by: PropertyRef = PropertyRef("updatedBy")
    condition: PropertyRef = PropertyRef("condition")
    description: PropertyRef = PropertyRef("description")
    delegated_managed_identity_resource_id: PropertyRef = PropertyRef(
        "delegatedManagedIdentityResourceId"
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    subscription_id: PropertyRef = PropertyRef(
        "AZURE_SUBSCRIPTION_ID", set_in_kwargs=True
    )


@dataclass(frozen=True)
class AzureRoleDefinitionProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name")
    type: PropertyRef = PropertyRef("type")
    role_name: PropertyRef = PropertyRef("roleName")
    description: PropertyRef = PropertyRef("description")
    assignable_scopes: PropertyRef = PropertyRef("assignableScopes")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    subscription_id: PropertyRef = PropertyRef(
        "AZURE_SUBSCRIPTION_ID", set_in_kwargs=True
    )


@dataclass(frozen=True)
class AzurePermissionsProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    actions: PropertyRef = PropertyRef("actions")
    not_actions: PropertyRef = PropertyRef("not_actions")
    data_actions: PropertyRef = PropertyRef("data_actions")
    not_data_actions: PropertyRef = PropertyRef("not_data_actions")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    subscription_id: PropertyRef = PropertyRef(
        "AZURE_SUBSCRIPTION_ID", set_in_kwargs=True
    )


# Relationship Properties for standard relationships
@dataclass(frozen=True)
class AzureRoleAssignmentToSubscriptionRelProperties(CartographyRelProperties):
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
class AzureRoleDefinitionToSubscriptionRel(CartographyRelSchema):
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
class AzureRoleDefinitionSchema(CartographyNodeSchema):
    label: str = "AzureRoleDefinition"
    properties: AzureRoleDefinitionProperties = AzureRoleDefinitionProperties()
    sub_resource_relationship: AzureRoleDefinitionToSubscriptionRel = (
        AzureRoleDefinitionToSubscriptionRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AzureRoleDefinitionToPermissionsRel(),
        ]
    )


@dataclass(frozen=True)
class AzurePermissionsSchema(CartographyNodeSchema):
    label: str = "AzurePermissions"
    properties: AzurePermissionsProperties = AzurePermissionsProperties()
    sub_resource_relationship: AzurePermissionsToSubscriptionRel = (
        AzurePermissionsToSubscriptionRel()
    )
