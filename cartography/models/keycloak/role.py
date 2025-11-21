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
class KeycloakRoleNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name", extra_index=True)
    description: PropertyRef = PropertyRef("description")
    scope_param_required: PropertyRef = PropertyRef("scopeParamRequired")
    composite: PropertyRef = PropertyRef("composite")
    client_role: PropertyRef = PropertyRef("clientRole")
    container_id: PropertyRef = PropertyRef("containerId")
    # We need to store the realm name because role are often referenced by name
    # and not by id, so we need to be able to find the role by name (that is not unique across realms)
    realm: PropertyRef = PropertyRef("REALM", set_in_kwargs=True, extra_index=True)
    lastupdated: PropertyRef = PropertyRef("LASTUPDATED", set_in_kwargs=True)


@dataclass(frozen=True)
class KeycloakRoleToRealmRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("LASTUPDATED", set_in_kwargs=True)


@dataclass(frozen=True)
# (:KeycloakRole)<-[:RESOURCE]-(:KeycloakRealm)
class KeycloakRoleToRealmRel(CartographyRelSchema):
    target_node_label: str = "KeycloakRealm"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"name": PropertyRef("REALM", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: KeycloakRoleToRealmRelProperties = KeycloakRoleToRealmRelProperties()


@dataclass(frozen=True)
class KeycloakRoleToClientRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("LASTUPDATED", set_in_kwargs=True)


@dataclass(frozen=True)
# (:KeycloakRole)<-[:DEFINES]->(:KeycloakClient)
class KeycloakRoleToClientRel(CartographyRelSchema):
    target_node_label: str = "KeycloakClient"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("containerId")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "DEFINES"
    properties: KeycloakRoleToClientRelProperties = KeycloakRoleToClientRelProperties()


@dataclass(frozen=True)
class KeycloakRoleToRoleRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("LASTUPDATED", set_in_kwargs=True)


@dataclass(frozen=True)
# (:KeycloakRole)-[:INCLUDES]->(:KeycloakRole)
class KeycloakRoleToRoleRel(CartographyRelSchema):
    target_node_label: str = "KeycloakRole"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("_composite_roles", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "INCLUDES"
    properties: KeycloakRoleToRoleRelProperties = KeycloakRoleToRoleRelProperties()


@dataclass(frozen=True)
class KeycloakRoleToScopeRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("LASTUPDATED", set_in_kwargs=True)


@dataclass(frozen=True)
# (:KeycloakRole)-[:GRANTS]->(:KeycloakScope)
class KeycloakRoleToScopeRel(CartographyRelSchema):
    target_node_label: str = "KeycloakScope"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("_scope_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "GRANTS"
    properties: KeycloakRoleToScopeRelProperties = KeycloakRoleToScopeRelProperties()


@dataclass(frozen=True)
class KeycloakRoleToUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("LASTUPDATED", set_in_kwargs=True)


@dataclass(frozen=True)
# (:KeycloakRole)<-[:ASSUME_ROLE]-(:KeycloakUser)
class KeycloakRoleToUserRel(CartographyRelSchema):
    target_node_label: str = "KeycloakUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("_direct_members", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "ASSUME_ROLE"
    properties: KeycloakRoleToUserRelProperties = KeycloakRoleToUserRelProperties()


@dataclass(frozen=True)
class KeycloakRoleSchema(CartographyNodeSchema):
    label: str = "KeycloakRole"
    properties: KeycloakRoleNodeProperties = KeycloakRoleNodeProperties()
    sub_resource_relationship: KeycloakRoleToRealmRel = KeycloakRoleToRealmRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            KeycloakRoleToClientRel(),
            KeycloakRoleToRoleRel(),
            KeycloakRoleToScopeRel(),
            KeycloakRoleToUserRel(),
        ],
    )
