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
class KeycloakGroupNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name")
    description: PropertyRef = PropertyRef("description")
    path: PropertyRef = PropertyRef("path")
    lastupdated: PropertyRef = PropertyRef("LASTUPDATED", set_in_kwargs=True)


@dataclass(frozen=True)
class KeycloakGroupToRealmRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("LASTUPDATED", set_in_kwargs=True)


@dataclass(frozen=True)
# (:KeycloakGroup)<-[:RESOURCE]-(:KeycloakRealm)
class KeycloakGroupToRealmRel(CartographyRelSchema):
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
# (:KeycloakGroup)-[:SUBGROUP_OF]->(:KeycloakGroup)
class KeycloakGroupToGroupRel(CartographyRelSchema):
    target_node_label: str = "KeycloakGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("parentId")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "SUBGROUP_OF"
    properties: KeycloakGroupToGroupRelProperties = KeycloakGroupToGroupRelProperties()


@dataclass(frozen=True)
class KeycloakGroupToUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("LASTUPDATED", set_in_kwargs=True)


@dataclass(frozen=True)
# (:KeycloakGroup)<-[:MEMBER_OF]-(:KeycloakUser)
class KeycloakGroupToUserRel(CartographyRelSchema):
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
# (:KeycloakGroup)-[:GRANTS]->(:KeycloakRole)
class KeycloakGroupToRoleRel(CartographyRelSchema):
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
class KeycloakGroupSchema(CartographyNodeSchema):
    label: str = "KeycloakGroup"
    properties: KeycloakGroupNodeProperties = KeycloakGroupNodeProperties()
    sub_resource_relationship: KeycloakGroupToRealmRel = KeycloakGroupToRealmRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [KeycloakGroupToGroupRel(), KeycloakGroupToUserRel(), KeycloakGroupToRoleRel()]
    )
