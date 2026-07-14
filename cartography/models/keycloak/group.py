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
class KeycloakGroupNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="The unique identifier of the group"
    )
    name: PropertyRef = PropertyRef("name", description="The name of the group")
    description: PropertyRef = PropertyRef(
        "description", description="The description of the group"
    )
    path: PropertyRef = PropertyRef(
        "path", description="The hierarchical path of the group"
    )
    lastupdated: PropertyRef = PropertyRef(
        "LASTUPDATED",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )


@dataclass(frozen=True)
class KeycloakGroupToRealmRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("LASTUPDATED", set_in_kwargs=True)


@dataclass(frozen=True)
# (:KeycloakGroup)<-[:RESOURCE]-(:KeycloakRealm)
class KeycloakGroupToRealmRel(CartographyRelSchema):
    """The realm contains the group."""

    target_node_label: str = "KeycloakRealm"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"name": PropertyRef("REALM", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: KeycloakGroupToRealmRelProperties = KeycloakGroupToRealmRelProperties()


@dataclass(frozen=True)
class KeycloakGroupToGroupRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("LASTUPDATED", set_in_kwargs=True)


@dataclass(frozen=True)
# DEPRECATED: replaced by the canonical (:UserGroup)-[:MEMBER_OF]->(:UserGroup)
# edge (KeycloakGroupToGroupMemberOfRel). Kept for backward compatibility, will
# be removed in v1.0.0.
# (:KeycloakGroup)-[:SUBGROUP_OF]->(:KeycloakGroup)
class KeycloakGroupToGroupRel(CartographyRelSchema):
    """Deprecated compatibility edge linking a subgroup to its parent group."""

    target_node_label: str = "KeycloakGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("parentId")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "SUBGROUP_OF"
    properties: KeycloakGroupToGroupRelProperties = KeycloakGroupToGroupRelProperties()


@dataclass(frozen=True)
class KeycloakGroupToGroupMemberOfRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("LASTUPDATED", set_in_kwargs=True)


@dataclass(frozen=True)
# Canonical ontology edge: (:UserGroup)-[:MEMBER_OF]->(:UserGroup)
class KeycloakGroupToGroupMemberOfRel(CartographyRelSchema):
    """The group is a member of its parent group."""

    target_node_label: str = "KeycloakGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("parentId")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MEMBER_OF"
    properties: KeycloakGroupToGroupMemberOfRelProperties = (
        KeycloakGroupToGroupMemberOfRelProperties()
    )


@dataclass(frozen=True)
class KeycloakGroupToUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("LASTUPDATED", set_in_kwargs=True)


@dataclass(frozen=True)
# (:KeycloakGroup)<-[:MEMBER_OF]-(:KeycloakUser)
class KeycloakGroupToUserRel(CartographyRelSchema):
    """Users can be members of the group."""

    target_node_label: str = "KeycloakUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("_member_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "MEMBER_OF"
    properties: KeycloakGroupToUserRelProperties = KeycloakGroupToUserRelProperties()


@dataclass(frozen=True)
class KeycloakGroupToRoleRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("LASTUPDATED", set_in_kwargs=True)


@dataclass(frozen=True)
# DEPRECATED: replaced by the canonical (:UserGroup)-[:HAS_ROLE]->(:PermissionRole)
# edge (KeycloakGroupToRoleHasRoleRel). Kept for backward compatibility, will be
# removed in v1.0.0.
# (:KeycloakGroup)-[:GRANTS]->(:KeycloakRole)
class KeycloakGroupToRoleRel(CartographyRelSchema):
    """Deprecated compatibility edge for a role granted to group members."""

    target_node_label: str = "KeycloakRole"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "name": PropertyRef("_roles", one_to_many=True),
            "realm": PropertyRef("REALM", set_in_kwargs=True),
        },
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "GRANTS"
    properties: KeycloakGroupToRoleRelProperties = KeycloakGroupToRoleRelProperties()


@dataclass(frozen=True)
class KeycloakGroupToRoleHasRoleRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("LASTUPDATED", set_in_kwargs=True)


@dataclass(frozen=True)
# Canonical ontology edge: (:UserGroup)-[:HAS_ROLE]->(:PermissionRole)
class KeycloakGroupToRoleHasRoleRel(CartographyRelSchema):
    """The group has a role that applies to its members."""

    target_node_label: str = "KeycloakRole"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "name": PropertyRef("_roles", one_to_many=True),
            "realm": PropertyRef("REALM", set_in_kwargs=True),
        },
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_ROLE"
    properties: KeycloakGroupToRoleHasRoleRelProperties = (
        KeycloakGroupToRoleHasRoleRelProperties()
    )


@dataclass(frozen=True)
class KeycloakGroupSchema(CartographyNodeSchema):
    """Represents a group of users in Keycloak that can be used for organizing users and assigning roles."""

    label: str = "KeycloakGroup"
    properties: KeycloakGroupNodeProperties = KeycloakGroupNodeProperties()
    sub_resource_relationship: KeycloakGroupToRealmRel = KeycloakGroupToRealmRel()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["UserGroup"])
    other_relationships: OtherRelationships = OtherRelationships(
        [
            KeycloakGroupToGroupRel(),
            KeycloakGroupToGroupMemberOfRel(),
            KeycloakGroupToUserRel(),
            KeycloakGroupToRoleRel(),
            KeycloakGroupToRoleHasRoleRel(),
        ]
    )
