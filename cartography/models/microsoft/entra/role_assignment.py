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
class EntraRoleAssignmentNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Entra role assignment ID.")
    role_definition_id: PropertyRef = PropertyRef(
        "role_definition_id",
        extra_index=True,
        description="ID of the assigned role definition.",
    )
    principal_id: PropertyRef = PropertyRef(
        "principal_id",
        extra_index=True,
        description="ID of the principal granted the role.",
    )
    directory_scope_id: PropertyRef = PropertyRef(
        "directory_scope_id", description="Directory scope of the assignment."
    )
    app_scope_id: PropertyRef = PropertyRef(
        "app_scope_id", description="Application-specific scope of the assignment."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the latest Cartography update.",
    )


@dataclass(frozen=True)
class EntraRoleAssignmentToTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:EntraRoleAssignment)<-[:RESOURCE]-(:AzureTenant)
class EntraRoleAssignmentToTenantRel(CartographyRelSchema):
    """Links a Microsoft tenant to one of its directory role assignments."""

    target_node_label: str = "AzureTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TENANT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: EntraRoleAssignmentToTenantRelProperties = (
        EntraRoleAssignmentToTenantRelProperties()
    )


@dataclass(frozen=True)
class EntraRoleAssignmentToRoleDefinitionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:EntraRoleAssignment)-[:ASSIGNED_TO]->(:EntraRoleDefinition)
class EntraRoleAssignmentToRoleDefinitionRel(CartographyRelSchema):
    """Links a role assignment to the directory role it grants."""

    target_node_label: str = "EntraRoleDefinition"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("role_definition_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ASSIGNED_TO"
    properties: EntraRoleAssignmentToRoleDefinitionRelProperties = (
        EntraRoleAssignmentToRoleDefinitionRelProperties()
    )


@dataclass(frozen=True)
class EntraRoleAssignmentToUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:EntraUser)-[:HAS_ROLE]->(:EntraRoleAssignment)
class EntraRoleAssignmentToUserRel(CartographyRelSchema):
    """Links an Entra user to a directory role assignment they hold."""

    target_node_label: str = "EntraUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("principal_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_ROLE"
    properties: EntraRoleAssignmentToUserRelProperties = (
        EntraRoleAssignmentToUserRelProperties()
    )


@dataclass(frozen=True)
class EntraRoleAssignmentToGroupRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:EntraGroup)-[:HAS_ROLE]->(:EntraRoleAssignment)
class EntraRoleAssignmentToGroupRel(CartographyRelSchema):
    """Links an Entra group to a directory role assignment it holds."""

    target_node_label: str = "EntraGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("principal_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_ROLE"
    properties: EntraRoleAssignmentToGroupRelProperties = (
        EntraRoleAssignmentToGroupRelProperties()
    )


@dataclass(frozen=True)
class EntraRoleAssignmentToServicePrincipalRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:EntraServicePrincipal)-[:HAS_ROLE]->(:EntraRoleAssignment)
class EntraRoleAssignmentToServicePrincipalRel(CartographyRelSchema):
    """Links a service principal to a directory role assignment it holds."""

    target_node_label: str = "EntraServicePrincipal"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("principal_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_ROLE"
    properties: EntraRoleAssignmentToServicePrincipalRelProperties = (
        EntraRoleAssignmentToServicePrincipalRelProperties()
    )


@dataclass(frozen=True)
class EntraRoleAssignmentSchema(CartographyNodeSchema):
    """A directory role assignment in Microsoft Entra ID."""

    label: str = "EntraRoleAssignment"
    properties: EntraRoleAssignmentNodeProperties = EntraRoleAssignmentNodeProperties()
    sub_resource_relationship: EntraRoleAssignmentToTenantRel = (
        EntraRoleAssignmentToTenantRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            EntraRoleAssignmentToRoleDefinitionRel(),
            EntraRoleAssignmentToUserRel(),
            EntraRoleAssignmentToGroupRel(),
            EntraRoleAssignmentToServicePrincipalRel(),
        ],
    )
