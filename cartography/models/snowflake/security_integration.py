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
from cartography.models.ontology.labels import IDENTITY_PROVIDER
from cartography.models.snowflake.extra_labels import SNOWFLAKE_SECURABLE


@dataclass(frozen=True)
class SnowflakeSecurityIntegrationNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Account-scoped identifier for the security integration."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="The security integration name."
    )
    integration_type: PropertyRef = PropertyRef(
        "integration_type",
        description=(
            "Snowflake integration type, for example SAML2, EXTERNAL_OAUTH, OAUTH or "
            "SCIM, optionally suffixed with the provider."
        ),
    )
    category: PropertyRef = PropertyRef(
        "category", description="Snowflake integration category."
    )
    protocol: PropertyRef = PropertyRef(
        "protocol",
        description=(
            "Federation protocol derived from the integration type: SAML, OIDC or SCIM. "
            "Null when the type maps to none of them."
        ),
    )
    enabled: PropertyRef = PropertyRef(
        "enabled", description="Whether the integration is active."
    )
    saml2_issuer: PropertyRef = PropertyRef(
        "saml2_issuer",
        extra_index=True,
        description="Entity id of the SAML identity provider that signs assertions.",
    )
    saml2_sso_url: PropertyRef = PropertyRef(
        "saml2_sso_url",
        description="URL users are redirected to for SAML single sign-on.",
    )
    saml2_provider: PropertyRef = PropertyRef(
        "saml2_provider",
        description="SAML provider name, for example OKTA, ADFS or CUSTOM.",
    )
    saml2_x509_cert_fingerprint: PropertyRef = PropertyRef(
        "saml2_x509_cert_fingerprint",
        description=(
            "SHA-256 fingerprint of the identity provider's signing certificate. Only "
            "the fingerprint is stored, never the certificate body."
        ),
    )
    external_oauth_issuer: PropertyRef = PropertyRef(
        "external_oauth_issuer",
        extra_index=True,
        description="Issuer claim the external OAuth authorization server must present.",
    )
    external_oauth_jws_keys_url: PropertyRef = PropertyRef(
        "external_oauth_jws_keys_url",
        description="URL Snowflake fetches the authorization server's signing keys from.",
    )
    external_oauth_audience_list: PropertyRef = PropertyRef(
        "external_oauth_audience_list",
        description="Audience values Snowflake accepts in an external OAuth token.",
    )
    external_oauth_any_role_mode: PropertyRef = PropertyRef(
        "external_oauth_any_role_mode",
        description=(
            "Whether a token may request any role rather than only the roles named in "
            "its scope. ENABLE lets a token holder pick any role the user has."
        ),
    )
    oauth_client_type: PropertyRef = PropertyRef(
        "oauth_client_type",
        description=(
            "Whether the Snowflake OAuth client is CONFIDENTIAL or PUBLIC. A public "
            "client authenticates without a secret."
        ),
    )
    oauth_redirect_uri: PropertyRef = PropertyRef(
        "oauth_redirect_uri",
        description="Redirect URI authorization codes are returned to.",
    )
    oauth_issue_refresh_tokens: PropertyRef = PropertyRef(
        "oauth_issue_refresh_tokens",
        description="Whether the integration issues long-lived refresh tokens.",
    )
    oauth_refresh_token_validity: PropertyRef = PropertyRef(
        "oauth_refresh_token_validity",
        description="Seconds a refresh token issued by the integration stays valid.",
    )
    scim_client: PropertyRef = PropertyRef(
        "scim_client",
        description="SCIM client provisioning users and roles, for example OKTA or AZURE.",
    )
    run_as_role: PropertyRef = PropertyRef(
        "run_as_role",
        description=(
            "Name of the Snowflake role the SCIM client acts as, which bounds what the "
            "external provisioner may create and modify."
        ),
    )
    network_policy: PropertyRef = PropertyRef(
        "network_policy",
        description="Name of the network policy restricting where the integration may be used from.",
    )
    comment: PropertyRef = PropertyRef(
        "comment", description="Security integration comment."
    )
    created_on: PropertyRef = PropertyRef(
        "created_on", description="When the security integration was created."
    )


@dataclass(frozen=True)
class SnowflakeSecurityIntegrationToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeAccount)-[:RESOURCE]->(:SnowflakeSecurityIntegration)
class SnowflakeSecurityIntegrationToAccountRel(CartographyRelSchema):
    """A Snowflake account contains the security integration as a resource."""

    target_node_label: str = "SnowflakeAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SnowflakeSecurityIntegrationToAccountRelProperties = (
        SnowflakeSecurityIntegrationToAccountRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeSecurityIntegrationToRoleRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeSecurityIntegration)-[:RUNS_AS_ROLE]->(:SnowflakeRole)
class SnowflakeSecurityIntegrationToRoleRel(CartographyRelSchema):
    """A Snowflake security integration acts as this role when provisioning through SCIM."""

    target_node_label: str = "SnowflakeRole"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("run_as_role_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "RUNS_AS_ROLE"
    properties: SnowflakeSecurityIntegrationToRoleRelProperties = (
        SnowflakeSecurityIntegrationToRoleRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeSecurityIntegrationToNetworkPolicyRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeSecurityIntegration)-[:GOVERNED_BY]->(:SnowflakeNetworkPolicy)
class SnowflakeSecurityIntegrationToNetworkPolicyRel(CartographyRelSchema):
    """Use of this Snowflake security integration is restricted by a network policy."""

    target_node_label: str = "SnowflakeNetworkPolicy"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("network_policy_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "GOVERNED_BY"
    properties: SnowflakeSecurityIntegrationToNetworkPolicyRelProperties = (
        SnowflakeSecurityIntegrationToNetworkPolicyRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeSecurityIntegrationSchema(CartographyNodeSchema):
    """Represents a Snowflake security integration: the federated sign-in, OAuth or SCIM trust configured on the account."""

    label: str = "SnowflakeSecurityIntegration"
    properties: SnowflakeSecurityIntegrationNodeProperties = (
        SnowflakeSecurityIntegrationNodeProperties()
    )
    # IdentityProvider: ontology label; a security integration is the external
    # identity source Snowflake accepts authentication from.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        [IDENTITY_PROVIDER, SNOWFLAKE_SECURABLE],
    )
    sub_resource_relationship: SnowflakeSecurityIntegrationToAccountRel = (
        SnowflakeSecurityIntegrationToAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            SnowflakeSecurityIntegrationToRoleRel(),
            SnowflakeSecurityIntegrationToNetworkPolicyRel(),
        ],
    )
