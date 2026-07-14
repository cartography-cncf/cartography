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
    id: PropertyRef = PropertyRef(
        "id", description="The unique identifier of the scope"
    )
    name: PropertyRef = PropertyRef(
        "name",
        extra_index=True,
        description="The name of the scope (indexed for queries)",
    )
    description: PropertyRef = PropertyRef(
        "description", description="The description of the scope"
    )
    protocol: PropertyRef = PropertyRef(
        "protocol", description="The protocol associated with the scope"
    )
    include_in_token_scope: PropertyRef = PropertyRef(
        "attributes.include.in.token.scope",
        description="Whether to include in token scope",
    )
    display_on_consent_screen: PropertyRef = PropertyRef(
        "attributes.display.on.consent.screen",
        description="Whether to display on consent screen",
    )
    # We need to store the realm name because scope are often referenced by name
    # and not by id, so we need to be able to find the scope by name (that is not unique across realms)
    realm: PropertyRef = PropertyRef(
        "REALM",
        set_in_kwargs=True,
        extra_index=True,
        description="The realm name for scope lookup (indexed)",
    )
    lastupdated: PropertyRef = PropertyRef(
        "LASTUPDATED",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )


@dataclass(frozen=True)
class KeycloakScopeToRealmRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("LASTUPDATED", set_in_kwargs=True)


@dataclass(frozen=True)
# (:KeycloakScope)<-[:RESOURCE]-(:KeycloakRealm)
class KeycloakScopeToRealmRel(CartographyRelSchema):
    """The realm contains the client scope."""

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
    """The role grants a client scope."""

    target_node_label: str = "KeycloakRole"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("_role_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "GRANTS"
    properties: KeycloakScopeToRoleRelProperties = KeycloakScopeToRoleRelProperties()


@dataclass(frozen=True)
class KeycloakScopeSchema(CartographyNodeSchema):
    """Represents a client scope in Keycloak that defines what access is requested or granted."""

    label: str = "KeycloakScope"
    properties: KeycloakScopeNodeProperties = KeycloakScopeNodeProperties()
    sub_resource_relationship: KeycloakScopeToRealmRel = KeycloakScopeToRealmRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [KeycloakScopeToRoleRel()],
    )
