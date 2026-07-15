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
    id: PropertyRef = PropertyRef(
        "id", description="The unique identifier of the authentication flow"
    )
    alias: PropertyRef = PropertyRef(
        "alias",
        extra_index=True,
        description="The alias of the authentication flow (indexed for queries)",
    )
    description: PropertyRef = PropertyRef(
        "description", description="The description of the authentication flow"
    )
    provider_id: PropertyRef = PropertyRef(
        "providerId", description="The provider identifier for the authentication flow"
    )
    top_level: PropertyRef = PropertyRef(
        "topLevel", description="Whether this is a top-level authentication flow"
    )
    built_in: PropertyRef = PropertyRef(
        "builtIn", description="Whether this is a built-in authentication flow"
    )
    lastupdated: PropertyRef = PropertyRef(
        "LASTUPDATED",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )
    # We need to store the realm name because authentication flows are often referenced by name
    # and not by id, so we need to be able to find the authentication flows by name (that is not unique across realms)
    realm: PropertyRef = PropertyRef(
        "REALM",
        set_in_kwargs=True,
        extra_index=True,
        description="The realm name for flow lookup (indexed)",
    )


@dataclass(frozen=True)
class KeycloakAuthenticationFlowToRealmRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("LASTUPDATED", set_in_kwargs=True)


@dataclass(frozen=True)
# (:KeycloakAuthenticationFlow)<-[:RESOURCE]-(:KeycloakRealm)
class KeycloakAuthenticationFlowToRealmRel(CartographyRelSchema):
    """The realm contains the authentication flow."""

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
    """Represents an authentication flow in Keycloak that defines the sequence of authentication steps and requirements for user authentication. Authentication flows control how users authenticate to the realm and can include various authentication mechanisms and requirements."""

    label: str = "KeycloakAuthenticationFlow"
    properties: KeycloakAuthenticationFlowNodeProperties = (
        KeycloakAuthenticationFlowNodeProperties()
    )
    sub_resource_relationship: KeycloakAuthenticationFlowToRealmRel = (
        KeycloakAuthenticationFlowToRealmRel()
    )
