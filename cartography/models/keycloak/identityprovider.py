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
class KeycloakIdentityProviderNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("internalId")
    alias: PropertyRef = PropertyRef("alias", extra_index=True)
    display_name: PropertyRef = PropertyRef("displayName")
    provider_id: PropertyRef = PropertyRef("providerId")
    enabled: PropertyRef = PropertyRef("enabled")
    update_profile_first_login_mode: PropertyRef = PropertyRef(
        "updateProfileFirstLoginMode"
    )
    trust_email: PropertyRef = PropertyRef("trustEmail")
    store_token: PropertyRef = PropertyRef("storeToken")
    add_read_token_role_on_create: PropertyRef = PropertyRef("addReadTokenRoleOnCreate")
    authenticate_by_default: PropertyRef = PropertyRef("authenticateByDefault")
    link_only: PropertyRef = PropertyRef("linkOnly")
    hide_on_login: PropertyRef = PropertyRef("hideOnLogin")
    first_broker_login_flow_alias: PropertyRef = PropertyRef(
        "firstBrokerLoginFlowAlias"
    )
    post_broker_login_flow_alias: PropertyRef = PropertyRef("postBrokerLoginFlowAlias")
    organization_id: PropertyRef = PropertyRef("organizationId")
    update_profile_first_login: PropertyRef = PropertyRef("updateProfileFirstLogin")
    config_sync_mode: PropertyRef = PropertyRef("config.syncMode")
    lastupdated: PropertyRef = PropertyRef("LASTUPDATED", set_in_kwargs=True)


@dataclass(frozen=True)
class KeycloakIdentityProviderToRealmRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("LASTUPDATED", set_in_kwargs=True)


@dataclass(frozen=True)
# (:KeycloakIdentityProvider)<-[:RESOURCE]-(:KeycloakRealm)
class KeycloakIdentityProviderToRealmRel(CartographyRelSchema):
    target_node_label: str = "KeycloakRealm"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"name": PropertyRef("REALM", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: KeycloakIdentityProviderToRealmRelProperties = (
        KeycloakIdentityProviderToRealmRelProperties()
    )


@dataclass(frozen=True)
class KeycloakIdentityProviderToUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("LASTUPDATED", set_in_kwargs=True)


@dataclass(frozen=True)
# (:KeycloakIdentityProvider)<-[:HAS_IDENTITY]-(:KeycloakUser)
class KeycloakIdentityProviderToUserRel(CartographyRelSchema):
    target_node_label: str = "KeycloakUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("_member_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_IDENTITY"
    properties: KeycloakIdentityProviderToUserRelProperties = (
        KeycloakIdentityProviderToUserRelProperties()
    )


@dataclass(frozen=True)
class KeycloakIdentityProviderSchema(CartographyNodeSchema):
    label: str = "KeycloakIdentityProvider"
    properties: KeycloakIdentityProviderNodeProperties = (
        KeycloakIdentityProviderNodeProperties()
    )
    sub_resource_relationship: KeycloakIdentityProviderToRealmRel = (
        KeycloakIdentityProviderToRealmRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [KeycloakIdentityProviderToUserRel()],
    )
