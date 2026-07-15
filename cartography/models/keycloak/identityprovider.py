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
class KeycloakIdentityProviderNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "internalId", description="The internal unique identifier"
    )
    alias: PropertyRef = PropertyRef(
        "alias",
        extra_index=True,
        description="The alias of the identity provider (indexed for queries)",
    )
    display_name: PropertyRef = PropertyRef(
        "displayName", description="The display name of the identity provider"
    )
    provider_id: PropertyRef = PropertyRef(
        "providerId", description="The provider type identifier"
    )
    enabled: PropertyRef = PropertyRef(
        "enabled", description="Whether the identity provider is enabled"
    )
    update_profile_first_login_mode: PropertyRef = PropertyRef(
        "updateProfileFirstLoginMode", description="Profile update mode on first login"
    )
    trust_email: PropertyRef = PropertyRef(
        "trustEmail", description="Whether to trust email from the provider"
    )
    store_token: PropertyRef = PropertyRef(
        "storeToken", description="Whether to store tokens from the provider"
    )
    add_read_token_role_on_create: PropertyRef = PropertyRef(
        "addReadTokenRoleOnCreate",
        description="Whether to add read token role on create",
    )
    authenticate_by_default: PropertyRef = PropertyRef(
        "authenticateByDefault", description="Whether to authenticate by default"
    )
    link_only: PropertyRef = PropertyRef(
        "linkOnly", description="Whether this provider is for linking only"
    )
    hide_on_login: PropertyRef = PropertyRef(
        "hideOnLogin", description="Whether to hide on login page"
    )
    first_broker_login_flow_alias: PropertyRef = PropertyRef(
        "firstBrokerLoginFlowAlias", description="First broker login flow alias"
    )
    post_broker_login_flow_alias: PropertyRef = PropertyRef(
        "postBrokerLoginFlowAlias", description="Post broker login flow alias"
    )
    organization_id: PropertyRef = PropertyRef(
        "organizationId", description="Organization ID if applicable"
    )
    update_profile_first_login: PropertyRef = PropertyRef(
        "updateProfileFirstLogin",
        description="Whether to update profile on first login",
    )
    config_sync_mode: PropertyRef = PropertyRef(
        "config.syncMode", description="Configuration sync mode"
    )
    lastupdated: PropertyRef = PropertyRef(
        "LASTUPDATED",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )


@dataclass(frozen=True)
class KeycloakIdentityProviderToRealmRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("LASTUPDATED", set_in_kwargs=True)


@dataclass(frozen=True)
# (:KeycloakIdentityProvider)<-[:RESOURCE]-(:KeycloakRealm)
class KeycloakIdentityProviderToRealmRel(CartographyRelSchema):
    """The realm contains the identity provider."""

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
    """The user authenticates through the identity provider."""

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
    """Represents an external identity provider configured in Keycloak for federated authentication."""

    label: str = "KeycloakIdentityProvider"
    properties: KeycloakIdentityProviderNodeProperties = (
        KeycloakIdentityProviderNodeProperties()
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["IdentityProvider"])
    sub_resource_relationship: KeycloakIdentityProviderToRealmRel = (
        KeycloakIdentityProviderToRealmRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [KeycloakIdentityProviderToUserRel()],
    )
