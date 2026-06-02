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
    id: PropertyRef = PropertyRef("id")
    role_definition_id: PropertyRef = PropertyRef(
        "role_definition_id", extra_index=True
    )
    principal_id: PropertyRef = PropertyRef("principal_id", extra_index=True)
    directory_scope_id: PropertyRef = PropertyRef("directory_scope_id")
    app_scope_id: PropertyRef = PropertyRef("app_scope_id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EntraRoleAssignmentToTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:EntraRoleAssignment)<-[:RESOURCE]-(:EntraTenant)
class EntraRoleAssignmentToTenantRel(CartographyRelSchema):
    target_node_label: str = "EntraTenant"
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
