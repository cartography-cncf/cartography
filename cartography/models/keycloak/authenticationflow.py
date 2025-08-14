from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class KeycloakAuthenticationFlowNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    alias: PropertyRef = PropertyRef("alias", extra_index=True)
    description: PropertyRef = PropertyRef("description")
    provider_id: PropertyRef = PropertyRef("providerId")
    top_level: PropertyRef = PropertyRef("topLevel")
    built_in: PropertyRef = PropertyRef("builtIn")
    lastupdated: PropertyRef = PropertyRef("LASTUPDATED", set_in_kwargs=True)
    # We need to store the realm name because authentication flows are often referenced by name
    # and not by id, so we need to be able to find the authentication flows by name (that is not unique across realms)
    realm: PropertyRef = PropertyRef("REALM", set_in_kwargs=True, extra_index=True)


@dataclass(frozen=True)
class KeycloakAuthenticationFlowToRealmRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("LASTUPDATED", set_in_kwargs=True)


@dataclass(frozen=True)
# (:KeycloakAuthenticationFlow)<-[:RESOURCE]-(:KeycloakRealm)
class KeycloakAuthenticationFlowToRealmRel(CartographyRelSchema):
    target_node_label: str = "KeycloakRealm"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"name": PropertyRef("REALM", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: KeycloakAuthenticationFlowToRealmRelProperties = (
        KeycloakAuthenticationFlowToRealmRelProperties()
    )


@dataclass(frozen=True)
class KeycloakAuthenticationFlowSchema(CartographyNodeSchema):
    label: str = "KeycloakAuthenticationFlow"
    properties: KeycloakAuthenticationFlowNodeProperties = (
        KeycloakAuthenticationFlowNodeProperties()
    )
    sub_resource_relationship: KeycloakAuthenticationFlowToRealmRel = (
        KeycloakAuthenticationFlowToRealmRel()
    )
