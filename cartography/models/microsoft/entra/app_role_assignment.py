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
class EntraAppRoleAssignmentNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Entra app role assignment ID.")
    app_role_id: PropertyRef = PropertyRef(
        "app_role_id", description="ID of the assigned application role."
    )
    created_date_time: PropertyRef = PropertyRef(
        "created_date_time", description="Timestamp when the assignment was created."
    )
    principal_id: PropertyRef = PropertyRef(
        "principal_id", description="ID of the principal receiving the role."
    )
    principal_display_name: PropertyRef = PropertyRef(
        "principal_display_name", description="Display name of the assigned principal."
    )
    principal_type: PropertyRef = PropertyRef(
        "principal_type", description="Type of the assigned principal."
    )
    resource_display_name: PropertyRef = PropertyRef(
        "resource_display_name",
        description="Display name of the resource service principal.",
    )
    resource_id: PropertyRef = PropertyRef(
        "resource_id", description="ID of the resource service principal."
    )
    application_app_id: PropertyRef = PropertyRef(
        "application_app_id", description="Client ID of the assigned application."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the latest Cartography update.",
    )


@dataclass(frozen=True)
class EntraAppRoleAssignmentToTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EntraAppRoleAssignmentToTenantRel(CartographyRelSchema):
    """Links a Microsoft tenant to one of its app role assignments."""

    target_node_label: str = "AzureTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TENANT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: EntraAppRoleAssignmentToTenantRelProperties = (
        EntraAppRoleAssignmentToTenantRelProperties()
    )


@dataclass(frozen=True)
class EntraAppRoleAssignmentToApplicationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EntraAppRoleAssignmentToApplicationRel(CartographyRelSchema):
    """Links an app role assignment to its Entra application."""

    target_node_label: str = "EntraApplication"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"app_id": PropertyRef("application_app_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ASSIGNED_TO"
    properties: EntraAppRoleAssignmentToApplicationRelProperties = (
        EntraAppRoleAssignmentToApplicationRelProperties()
    )


@dataclass(frozen=True)
class EntraAppRoleAssignmentToUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EntraAppRoleAssignmentToUserRel(CartographyRelSchema):
    """Links an Entra user to an app role assignment they hold."""

    target_node_label: str = "EntraUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("principal_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_APP_ROLE"
    properties: EntraAppRoleAssignmentToUserRelProperties = (
        EntraAppRoleAssignmentToUserRelProperties()
    )


@dataclass(frozen=True)
class EntraAppRoleAssignmentToGroupRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EntraAppRoleAssignmentToGroupRel(CartographyRelSchema):
    """Links an Entra group to an app role assignment it holds."""

    target_node_label: str = "EntraGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("principal_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_APP_ROLE"
    properties: EntraAppRoleAssignmentToGroupRelProperties = (
        EntraAppRoleAssignmentToGroupRelProperties()
    )


@dataclass(frozen=True)
class EntraAppRoleAssignmentSchema(CartographyNodeSchema):
    """An application role assignment in Microsoft Entra ID."""

    label: str = "EntraAppRoleAssignment"
    properties: EntraAppRoleAssignmentNodeProperties = (
        EntraAppRoleAssignmentNodeProperties()
    )
    sub_resource_relationship: EntraAppRoleAssignmentToTenantRel = (
        EntraAppRoleAssignmentToTenantRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            EntraAppRoleAssignmentToApplicationRel(),
            EntraAppRoleAssignmentToUserRel(),
            EntraAppRoleAssignmentToGroupRel(),
        ],
    )
