from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_source_node_matcher
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import SourceNodeMatcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class KeycloakClientNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="The unique identifier of the client"
    )
    client_id: PropertyRef = PropertyRef(
        "clientId", description="The client identifier used in protocols"
    )
    name: PropertyRef = PropertyRef("name", description="The name of the client")
    description: PropertyRef = PropertyRef(
        "description", description="The description of the client"
    )
    type: PropertyRef = PropertyRef("type", description="The type of the client")
    root_url: PropertyRef = PropertyRef(
        "rootUrl", description="The root URL of the client"
    )
    admin_url: PropertyRef = PropertyRef(
        "adminUrl", description="The admin URL of the client"
    )
    base_url: PropertyRef = PropertyRef(
        "baseUrl", description="The base URL of the client"
    )
    surrogate_auth_required: PropertyRef = PropertyRef(
        "surrogateAuthRequired",
        description="Whether surrogate authentication is required",
    )
    enabled: PropertyRef = PropertyRef(
        "enabled", description="Whether the client is enabled"
    )
    always_display_in_console: PropertyRef = PropertyRef(
        "alwaysDisplayInConsole", description="Whether to always display in console"
    )
    client_authenticator_type: PropertyRef = PropertyRef(
        "clientAuthenticatorType", description="The client authenticator type"
    )
    registration_access_token: PropertyRef = PropertyRef(
        "registrationAccessToken", description="Registration access token"
    )
    not_before: PropertyRef = PropertyRef(
        "notBefore", description="Not before timestamp for security"
    )
    bearer_only: PropertyRef = PropertyRef(
        "bearerOnly", description="Whether this is a bearer-only client"
    )
    consent_required: PropertyRef = PropertyRef(
        "consentRequired", description="Whether user consent is required"
    )
    standard_flow_enabled: PropertyRef = PropertyRef(
        "standardFlowEnabled", description="Whether standard flow is enabled"
    )
    implicit_flow_enabled: PropertyRef = PropertyRef(
        "implicitFlowEnabled", description="Whether implicit flow is enabled"
    )
    direct_access_grants_enabled: PropertyRef = PropertyRef(
        "directAccessGrantsEnabled",
        description="Whether direct access grants are enabled",
    )
    service_accounts_enabled: PropertyRef = PropertyRef(
        "serviceAccountsEnabled", description="Whether service accounts are enabled"
    )
    authorization_services_enabled: PropertyRef = PropertyRef(
        "authorizationServicesEnabled",
        description="Whether authorization services are enabled",
    )
    direct_grants_only: PropertyRef = PropertyRef(
        "directGrantsOnly", description="Whether only direct grants are allowed"
    )
    public_client: PropertyRef = PropertyRef(
        "publicClient", description="Whether this is a public client"
    )
    frontchannel_logout: PropertyRef = PropertyRef(
        "frontchannelLogout", description="Whether frontchannel logout is enabled"
    )
    protocol: PropertyRef = PropertyRef(
        "protocol", description="The protocol used by the client"
    )
    full_scope_allowed: PropertyRef = PropertyRef(
        "fullScopeAllowed", description="Whether full scope is allowed"
    )
    node_re_registration_timeout: PropertyRef = PropertyRef(
        "nodeReRegistrationTimeout", description="Node re-registration timeout"
    )
    client_template: PropertyRef = PropertyRef(
        "clientTemplate", description="Client template reference"
    )
    use_template_config: PropertyRef = PropertyRef(
        "useTemplateConfig", description="Whether to use template config"
    )
    use_template_scope: PropertyRef = PropertyRef(
        "useTemplateScope", description="Whether to use template scope"
    )
    use_template_mappers: PropertyRef = PropertyRef(
        "useTemplateMappers", description="Whether to use template mappers"
    )
    origin: PropertyRef = PropertyRef("origin", description="Origin of the client")
    lastupdated: PropertyRef = PropertyRef(
        "LASTUPDATED",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )


@dataclass(frozen=True)
class KeycloakClientToRealmRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("LASTUPDATED", set_in_kwargs=True)


@dataclass(frozen=True)
# (:KeycloakClient)<-[:RESOURCE]-(:KeycloakRealm)
class KeycloakClientToRealmRel(CartographyRelSchema):
    """The realm contains the client."""

    target_node_label: str = "KeycloakRealm"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"name": PropertyRef("REALM", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: KeycloakClientToRealmRelProperties = (
        KeycloakClientToRealmRelProperties()
    )


@dataclass(frozen=True)
class KeycloakClientToDefaultScopeRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("LASTUPDATED", set_in_kwargs=True)


@dataclass(frozen=True)
# (:KeycloakClient)-[:HAS_DEFAULT_SCOPE]->(:KeycloakScope)
class KeycloakClientToDefaultScopeRel(CartographyRelSchema):
    """The client uses a default client scope."""

    target_node_label: str = "KeycloakScope"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "name": PropertyRef("defaultClientScopes", one_to_many=True),
            "realm": PropertyRef("REALM", set_in_kwargs=True),
        },
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_DEFAULT_SCOPE"
    properties: KeycloakClientToDefaultScopeRelProperties = (
        KeycloakClientToDefaultScopeRelProperties()
    )


@dataclass(frozen=True)
class KeycloakClientToOptionalScopeRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("LASTUPDATED", set_in_kwargs=True)


@dataclass(frozen=True)
# (:KeycloakClient)-[:HAS_OPTIONAL_SCOPE]->(:KeycloakScope)
class KeycloakClientToOptionalScopeRel(CartographyRelSchema):
    """The client can request an optional client scope."""

    target_node_label: str = "KeycloakScope"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "name": PropertyRef("optionalClientScopes", one_to_many=True),
            "realm": PropertyRef("REALM", set_in_kwargs=True),
        },
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_OPTIONAL_SCOPE"
    properties: KeycloakClientToOptionalScopeRelProperties = (
        KeycloakClientToOptionalScopeRelProperties()
    )


@dataclass(frozen=True)
class KeycloakClientToServiceAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("LASTUPDATED", set_in_kwargs=True)


@dataclass(frozen=True)
# (:KeycloakClient)-[:HAS_SERVICE_ACCOUNT]->(:KeycloakUser)
class KeycloakClientToServiceAccountRel(CartographyRelSchema):
    """The client uses a user as its service account."""

    target_node_label: str = "KeycloakUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("_service_account_user_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_SERVICE_ACCOUNT"
    properties: KeycloakClientToServiceAccountRelProperties = (
        KeycloakClientToServiceAccountRelProperties()
    )


@dataclass(frozen=True)
class KeycloakClientSchema(CartographyNodeSchema):
    """Represents a Keycloak client application that can request authentication and authorization services from the realm."""

    label: str = "KeycloakClient"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["ThirdPartyApp"])
    properties: KeycloakClientNodeProperties = KeycloakClientNodeProperties()
    sub_resource_relationship: KeycloakClientToRealmRel = KeycloakClientToRealmRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            KeycloakClientToDefaultScopeRel(),
            KeycloakClientToOptionalScopeRel(),
            KeycloakClientToServiceAccountRel(),
        ]
    )


# The following relationships are MatchLinks to enable batch loading with rel properties
@dataclass(frozen=True)
class KeycloakClientToFlowRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("LASTUPDATED", set_in_kwargs=True)
    flow_name: PropertyRef = PropertyRef("flow_name")
    default_flow: PropertyRef = PropertyRef("default_flow")
    # Mandatory fields for MatchLinks
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label", set_in_kwargs=True
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)


@dataclass(frozen=True)
# (:KeycloakClient)-[:USES]->(:KeycloakAuthenticationFlow)
class KeycloakClientToFlowMatchLink(CartographyRelSchema):
    """The client uses an authentication flow."""

    source_node_label: str = "KeycloakClient"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("client_id")},
    )
    target_node_label: str = "KeycloakAuthenticationFlow"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("flow_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES"
    properties: KeycloakClientToFlowRelProperties = KeycloakClientToFlowRelProperties()
