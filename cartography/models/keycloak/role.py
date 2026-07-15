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


@dataclass(frozen=True)
class KeycloakRoleNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="The unique identifier of the role")
    name: PropertyRef = PropertyRef(
        "name",
        extra_index=True,
        description="The name of the role (indexed for queries)",
    )
    description: PropertyRef = PropertyRef(
        "description", description="The description of the role"
    )
    scope_param_required: PropertyRef = PropertyRef(
        "scopeParamRequired", description="Whether scope parameter is required"
    )
    composite: PropertyRef = PropertyRef(
        "composite", description="Whether this is a composite role"
    )
    client_role: PropertyRef = PropertyRef(
        "clientRole", description="Whether this is a client-specific role"
    )
    container_id: PropertyRef = PropertyRef(
        "containerId", description="The container ID (realm or client)"
    )
    # We need to store the realm name because role are often referenced by name
    # and not by id, so we need to be able to find the role by name (that is not unique across realms)
    realm: PropertyRef = PropertyRef(
        "REALM",
        set_in_kwargs=True,
        extra_index=True,
        description="The realm name for role lookup (indexed)",
    )
    lastupdated: PropertyRef = PropertyRef(
        "LASTUPDATED",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )


@dataclass(frozen=True)
class KeycloakRoleToRealmRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("LASTUPDATED", set_in_kwargs=True)


@dataclass(frozen=True)
# (:KeycloakRole)<-[:RESOURCE]-(:KeycloakRealm)
class KeycloakRoleToRealmRel(CartographyRelSchema):
    """The realm contains the role."""

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
    """The client defines the role."""

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
    """The composite role includes another role."""

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
    """The role grants a client scope."""

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
# DEPRECATED: replaced by the canonical (:UserAccount)-[:HAS_ROLE]->(:PermissionRole)
# edge (KeycloakRoleToUserHasRoleRel). Kept for backward compatibility, will be
# removed in v1.0.0.
# (:KeycloakRole)<-[:ASSUME_ROLE]-(:KeycloakUser)
class KeycloakRoleToUserRel(CartographyRelSchema):
    """Deprecated compatibility edge for a role assumed by a user."""

    target_node_label: str = "KeycloakUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("_direct_members", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "ASSUME_ROLE"
    properties: KeycloakRoleToUserRelProperties = KeycloakRoleToUserRelProperties()


@dataclass(frozen=True)
class KeycloakRoleToUserHasRoleRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("LASTUPDATED", set_in_kwargs=True)


@dataclass(frozen=True)
# Canonical ontology edge: (:UserAccount)-[:HAS_ROLE]->(:PermissionRole)
# i.e. (:KeycloakRole)<-[:HAS_ROLE]-(:KeycloakUser)
class KeycloakRoleToUserHasRoleRel(CartographyRelSchema):
    """A user has the role directly or through group membership."""

    target_node_label: str = "KeycloakUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("_direct_members", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_ROLE"
    properties: KeycloakRoleToUserHasRoleRelProperties = (
        KeycloakRoleToUserHasRoleRelProperties()
    )


@dataclass(frozen=True)
class KeycloakRoleSchema(CartographyNodeSchema):
    """Represents a role in Keycloak that defines permissions and can be assigned to users or groups."""

    label: str = "KeycloakRole"
    properties: KeycloakRoleNodeProperties = KeycloakRoleNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["PermissionRole"])
    sub_resource_relationship: KeycloakRoleToRealmRel = KeycloakRoleToRealmRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            KeycloakRoleToClientRel(),
            KeycloakRoleToRoleRel(),
            KeycloakRoleToScopeRel(),
            KeycloakRoleToUserRel(),
            KeycloakRoleToUserHasRoleRel(),
        ],
    )
