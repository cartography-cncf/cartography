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
    id: PropertyRef = PropertyRef("id")
    client_id: PropertyRef = PropertyRef("clientId")
    name: PropertyRef = PropertyRef("name")
    description: PropertyRef = PropertyRef("description")
    type: PropertyRef = PropertyRef("type")
    root_url: PropertyRef = PropertyRef("rootUrl")
    admin_url: PropertyRef = PropertyRef("adminUrl")
    base_url: PropertyRef = PropertyRef("baseUrl")
    surrogate_auth_required: PropertyRef = PropertyRef("surrogateAuthRequired")
    enabled: PropertyRef = PropertyRef("enabled")
    always_display_in_console: PropertyRef = PropertyRef("alwaysDisplayInConsole")
    client_authenticator_type: PropertyRef = PropertyRef("clientAuthenticatorType")
    registration_access_token: PropertyRef = PropertyRef("registrationAccessToken")
    not_before: PropertyRef = PropertyRef("notBefore")
    bearer_only: PropertyRef = PropertyRef("bearerOnly")
    consent_required: PropertyRef = PropertyRef("consentRequired")
    standard_flow_enabled: PropertyRef = PropertyRef("standardFlowEnabled")
    implicit_flow_enabled: PropertyRef = PropertyRef("implicitFlowEnabled")
    direct_access_grants_enabled: PropertyRef = PropertyRef("directAccessGrantsEnabled")
    service_accounts_enabled: PropertyRef = PropertyRef("serviceAccountsEnabled")
    authorization_services_enabled: PropertyRef = PropertyRef(
        "authorizationServicesEnabled"
    )
    direct_grants_only: PropertyRef = PropertyRef("directGrantsOnly")
    public_client: PropertyRef = PropertyRef("publicClient")
    frontchannel_logout: PropertyRef = PropertyRef("frontchannelLogout")
    protocol: PropertyRef = PropertyRef("protocol")
    full_scope_allowed: PropertyRef = PropertyRef("fullScopeAllowed")
    node_re_registration_timeout: PropertyRef = PropertyRef("nodeReRegistrationTimeout")
    client_template: PropertyRef = PropertyRef("clientTemplate")
    use_template_config: PropertyRef = PropertyRef("useTemplateConfig")
    use_template_scope: PropertyRef = PropertyRef("useTemplateScope")
    use_template_mappers: PropertyRef = PropertyRef("useTemplateMappers")
    origin: PropertyRef = PropertyRef("origin")
    lastupdated: PropertyRef = PropertyRef("LASTUPDATED", set_in_kwargs=True)


@dataclass(frozen=True)
class KeycloakClientToRealmRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("LASTUPDATED", set_in_kwargs=True)


@dataclass(frozen=True)
# (:KeycloakClient)<-[:RESOURCE]-(:KeycloakRealm)
class KeycloakClientToRealmRel(CartographyRelSchema):
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
