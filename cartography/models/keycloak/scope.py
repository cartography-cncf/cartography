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
class KeycloakScopeNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name", extra_index=True)
    description: PropertyRef = PropertyRef("description")
    protocol: PropertyRef = PropertyRef("protocol")
    include_in_token_scope: PropertyRef = PropertyRef(
        "attributes.include.in.token.scope",
    )
    display_on_consent_screen: PropertyRef = PropertyRef(
        "attributes.display.on.consent.screen",
    )
    # We need to store the realm name because scope are often referenced by name
    # and not by id, so we need to be able to find the scope by name (that is not unique across realms)
    realm: PropertyRef = PropertyRef("REALM", set_in_kwargs=True, extra_index=True)
    lastupdated: PropertyRef = PropertyRef("LASTUPDATED", set_in_kwargs=True)


@dataclass(frozen=True)
class KeycloakScopeToRealmRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("LASTUPDATED", set_in_kwargs=True)


@dataclass(frozen=True)
# (:KeycloakScope)<-[:RESOURCE]-(:KeycloakRealm)
class KeycloakScopeToRealmRel(CartographyRelSchema):
    target_node_label: str = "KeycloakRealm"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"name": PropertyRef("REALM", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: KeycloakScopeToRealmRelProperties = KeycloakScopeToRealmRelProperties()


@dataclass(frozen=True)
class KeycloakScopeToRoleRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("LASTUPDATED", set_in_kwargs=True)


@dataclass(frozen=True)
# (:KeycloakScope)<-[:GRANTS]-(:KeycloakRole)
class KeycloakScopeToRoleRel(CartographyRelSchema):
    target_node_label: str = "KeycloakRole"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("_role_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "GRANTS"
    properties: KeycloakScopeToRoleRelProperties = KeycloakScopeToRoleRelProperties()


@dataclass(frozen=True)
class KeycloakScopeSchema(CartographyNodeSchema):
    label: str = "KeycloakScope"
    properties: KeycloakScopeNodeProperties = KeycloakScopeNodeProperties()
    sub_resource_relationship: KeycloakScopeToRealmRel = KeycloakScopeToRealmRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [KeycloakScopeToRoleRel()],
    )
