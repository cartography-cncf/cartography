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
from cartography.models.ontology.labels import PERMISSION_ROLE
from cartography.models.ontology.labels import THIRD_PARTY_APP


@dataclass(frozen=True)
class OktaApplicationNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Unique identifier for the Okta resource."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this resource.",
    )
    accessibility_error_redirect_url: PropertyRef = PropertyRef(
        "accessibility_error_redirect_url",
        description="Okta accessibility error redirect URL.",
    )

    accessibility_login_redirect_url: PropertyRef = PropertyRef(
        "accessibility_login_redirect_url",
        description="Okta accessibility login redirect URL.",
    )
    accessibility_self_service: PropertyRef = PropertyRef(
        "accessibility_self_service", description="Okta accessibility self service."
    )
    created: PropertyRef = PropertyRef("created", description="Okta created.")
    credentials_oauth_client_token_endpoint_auth_method: PropertyRef = PropertyRef(
        "credentials_oauth_client_token_endpoint_auth_method",
        description=(
            "How an OAuth app authenticates to Okta's token endpoint: "
            "`client_secret_basic`, `client_secret_post`, or `client_secret_jwt` "
            "with a shared secret, `private_key_jwt` with a private key, or `none` "
            "for a public client. Null for apps that are not OAuth clients."
        ),
    )
    credentials_signing_kid: PropertyRef = PropertyRef(
        "credentials_signing_kid", description="Okta credentials signing kid."
    )
    credentials_signing_last_rotated: PropertyRef = PropertyRef(
        "credentials_signing_last_rotated",
        description="Okta credentials signing last rotated.",
    )
    credentials_signing_next_rotation: PropertyRef = PropertyRef(
        "credentials_signing_next_rotation",
        description="Okta credentials signing next rotation.",
    )
    credentials_signing_rotation_mode: PropertyRef = PropertyRef(
        "credentials_signing_rotation_mode",
        description="Okta credentials signing rotation mode.",
    )
    credentials_signing_use: PropertyRef = PropertyRef(
        "credentials_signing_use", description="Okta credentials signing use."
    )
    credentials_user_name_template_push_status: PropertyRef = PropertyRef(
        "credentials_user_name_template_push_status",
        description="Okta credentials user name template push status.",
    )
    credentials_user_name_template_suffix: PropertyRef = PropertyRef(
        "credentials_user_name_template_suffix",
        description="Okta credentials user name template suffix.",
    )
    credentials_user_name_template_template: PropertyRef = PropertyRef(
        "credentials_user_name_template_template",
        description="Okta credentials user name template template.",
    )
    credentials_user_name_template_type: PropertyRef = PropertyRef(
        "credentials_user_name_template_type",
        description="Okta credentials user name template type.",
    )
    features: PropertyRef = PropertyRef("features", description="Okta features.")
    granted_scopes: PropertyRef = PropertyRef(
        "granted_scopes",
        description=(
            "Sorted Okta API scopes, such as `okta.users.read` or "
            "`okta.users.manage`, actively granted to this OAuth app. A "
            "`.manage` scope lets the app make changes, within the limits of its "
            "admin role (`OktaApplicationRole`). Null when the sync could not read "
            "grants for this app: the credential lacks `okta.appGrants.read` or an "
            "admin role that allows it, or the app is not an OIDC app. An empty "
            "list means the app has no grants."
        ),
    )
    label: PropertyRef = PropertyRef("label", description="Okta label.")
    last_updated: PropertyRef = PropertyRef(
        "last_updated", description="Okta last updated."
    )
    licensing_seat_count: PropertyRef = PropertyRef(
        "licensing_seat_count", description="Okta licensing seat count."
    )
    name: PropertyRef = PropertyRef("name", description="Okta name.")
    settings_app_acs_url: PropertyRef = PropertyRef(
        "settings_app_acs_url", description="Okta settings app ACS URL."
    )
    settings_app_button_field: PropertyRef = PropertyRef(
        "settings_app_button_field", description="Okta settings app button field."
    )
    settings_app_login_url_regex: PropertyRef = PropertyRef(
        "settings_app_login_url_regex", description="Okta settings app login URL regex."
    )
    settings_app_org_name: PropertyRef = PropertyRef(
        "settings_app_org_name", description="Okta settings app org name."
    )
    settings_app_password_field: PropertyRef = PropertyRef(
        "settings_app_password_field", description="Okta settings app password field."
    )
    settings_app_url: PropertyRef = PropertyRef(
        "settings_app_url", description="Okta settings app URL."
    )
    settings_app_username_field: PropertyRef = PropertyRef(
        "settings_app_username_field", description="Okta settings app username field."
    )
    settings_app_implicit_assignment: PropertyRef = PropertyRef(
        "settings_app_implicit_assignment",
        description="Okta settings app implicit assignment.",
    )
    settings_app_inline_hook_id: PropertyRef = PropertyRef(
        "settings_app_inline_hook_id", description="Okta settings app inline hook ID."
    )
    settings_notifications_vpn_help_url: PropertyRef = PropertyRef(
        "settings_notifications_vpn_help_url",
        description="Okta settings notifications VPN help URL.",
    )
    settings_notifications_vpn_message: PropertyRef = PropertyRef(
        "settings_notifications_vpn_message",
        description="Okta settings notifications VPN message.",
    )
    settings_notifications_vpn_network_connection: PropertyRef = PropertyRef(
        "settings_notifications_vpn_network_connection",
        description="Okta settings notifications VPN network connection.",
    )
    settings_notifications_vpn_network_exclude: PropertyRef = PropertyRef(
        "settings_notifications_vpn_network_exclude",
        description="Okta settings notifications VPN network exclude.",
    )
    settings_notifications_vpn_network_include: PropertyRef = PropertyRef(
        "settings_notifications_vpn_network_include",
        description="Okta settings notifications VPN network include.",
    )
    settings_notes_admin: PropertyRef = PropertyRef(
        "settings_notes_admin", description="Okta settings notes admin."
    )
    settings_notes_enduser: PropertyRef = PropertyRef(
        "settings_notes_enduser", description="Okta settings notes enduser."
    )
    settings_oauth_client_application_type: PropertyRef = PropertyRef(
        "settings_oauth_client_application_type",
        description="Okta settings OAuth client application type.",
    )
    settings_oauth_client_client_uri: PropertyRef = PropertyRef(
        "settings_oauth_client_client_uri",
        description="Okta settings OAuth client client URI.",
    )
    settings_oauth_client_consent_method: PropertyRef = PropertyRef(
        "settings_oauth_client_consent_method",
        description="Okta settings OAuth client consent method.",
    )
    settings_oauth_client_dpop_bound_access_tokens: PropertyRef = PropertyRef(
        "settings_oauth_client_dpop_bound_access_tokens",
        description=(
            "Whether Okta requires DPoP (Demonstrating Proof of Possession) from "
            "this OAuth app, binding its access tokens to a key it holds so a "
            "stolen token cannot be replayed. Null for apps that are not OAuth "
            "clients."
        ),
    )
    settings_oauth_client_grant_Type: PropertyRef = PropertyRef(
        "settings_oauth_client_grant_Type",
        description="Okta settings OAuth client grant type.",
    )
    settings_oauth_client_idp_initiated_login_default_scope: PropertyRef = PropertyRef(
        "settings_oauth_client_idp_initiated_login_default_scope",
        description="Okta settings OAuth client IdP initiated login default scope.",
    )
    settings_oauth_client_idp_initiated_login_mode: PropertyRef = PropertyRef(
        "settings_oauth_client_idp_initiated_login_mode",
        description="Okta settings OAuth client IdP initiated login mode.",
    )
    settings_oauth_client_initiate_login_uri: PropertyRef = PropertyRef(
        "settings_oauth_client_initiate_login_uri",
        description="Okta settings OAuth client initiate login URI.",
    )
    settings_oauth_client_logo_uri: PropertyRef = PropertyRef(
        "settings_oauth_client_logo_uri",
        description="Okta settings OAuth client logo URI.",
    )
    settings_oauth_client_policy_uri: PropertyRef = PropertyRef(
        "settings_oauth_client_policy_uri",
        description="Okta settings OAuth client policy URI.",
    )
    settings_oauth_client_post_logout_redirect_uris: PropertyRef = PropertyRef(
        "settings_oauth_client_post_logout_redirect_uris",
        description="Okta settings OAuth client post logout redirect uris.",
    )
    settings_oauth_client_redirect_uris: PropertyRef = PropertyRef(
        "settings_oauth_client_redirect_uris",
        description="Okta settings OAuth client redirect uris.",
    )
    settings_oauth_client_response_types: PropertyRef = PropertyRef(
        "settings_oauth_client_response_types",
        description="Okta settings OAuth client response types.",
    )
    settings_oauth_client_tos_uri: PropertyRef = PropertyRef(
        "settings_oauth_client_tos_uri",
        description="Okta settings OAuth client tos URI.",
    )
    settings_oauth_client_wildcard_redirect: PropertyRef = PropertyRef(
        "settings_oauth_client_wildcard_redirect",
        description="Okta settings OAuth client wildcard redirect.",
    )
    # SAML sign-on configuration properties
    settings_sign_on_default_relay_state: PropertyRef = PropertyRef(
        "settings_sign_on_default_relay_state",
        description="Okta settings sign on default relay state.",
    )
    settings_sign_on_sso_acs_url: PropertyRef = PropertyRef(
        "settings_sign_on_sso_acs_url", description="Okta settings sign on SSO ACS URL."
    )
    settings_sign_on_sso_acs_url_override: PropertyRef = PropertyRef(
        "settings_sign_on_sso_acs_url_override",
        description="Okta settings sign on SSO ACS URL override.",
    )
    settings_sign_on_recipient: PropertyRef = PropertyRef(
        "settings_sign_on_recipient", description="Okta settings sign on recipient."
    )
    settings_sign_on_recipient_override: PropertyRef = PropertyRef(
        "settings_sign_on_recipient_override",
        description="Okta settings sign on recipient override.",
    )
    settings_sign_on_destination: PropertyRef = PropertyRef(
        "settings_sign_on_destination", description="Okta settings sign on destination."
    )
    settings_sign_on_destination_override: PropertyRef = PropertyRef(
        "settings_sign_on_destination_override",
        description="Okta settings sign on destination override.",
    )
    settings_sign_on_audience: PropertyRef = PropertyRef(
        "settings_sign_on_audience", description="Okta settings sign on audience."
    )
    settings_sign_on_audience_override: PropertyRef = PropertyRef(
        "settings_sign_on_audience_override",
        description="Okta settings sign on audience override.",
    )
    settings_sign_on_idp_issuer: PropertyRef = PropertyRef(
        "settings_sign_on_idp_issuer", description="Okta settings sign on IdP issuer."
    )
    settings_sign_on_subject_name_id_template: PropertyRef = PropertyRef(
        "settings_sign_on_subject_name_id_template",
        description="Okta settings sign on subject name ID template.",
    )
    settings_sign_on_subject_name_id_format: PropertyRef = PropertyRef(
        "settings_sign_on_subject_name_id_format",
        description="Okta settings sign on subject name ID format.",
    )
    settings_sign_on_response_signed: PropertyRef = PropertyRef(
        "settings_sign_on_response_signed",
        description="Okta settings sign on response signed.",
    )
    settings_sign_on_assertion_signed: PropertyRef = PropertyRef(
        "settings_sign_on_assertion_signed",
        description="Okta settings sign on assertion signed.",
    )
    settings_sign_on_signature_algorithm: PropertyRef = PropertyRef(
        "settings_sign_on_signature_algorithm",
        description="Okta settings sign on signature algorithm.",
    )
    settings_sign_on_digest_algorithm: PropertyRef = PropertyRef(
        "settings_sign_on_digest_algorithm",
        description="Okta settings sign on digest algorithm.",
    )
    settings_sign_on_honor_force_authn: PropertyRef = PropertyRef(
        "settings_sign_on_honor_force_authn",
        description="Okta settings sign on honor force authn.",
    )
    settings_sign_on_authn_context_class_ref: PropertyRef = PropertyRef(
        "settings_sign_on_authn_context_class_ref",
        description="Okta settings sign on authn context class ref.",
    )
    sign_on_mode: PropertyRef = PropertyRef(
        "sign_on_mode", description="Okta sign on mode."
    )
    status: PropertyRef = PropertyRef("status", description="Okta status.")
    activated: PropertyRef = PropertyRef("activated", description="Okta activated.")
    visibility_app_links: PropertyRef = PropertyRef(
        "visibility_app_links", description="Okta visibility app links."
    )
    visibility_auto_launch: PropertyRef = PropertyRef(
        "visibility_auto_launch", description="Okta visibility auto launch."
    )
    visibility_auto_submit_toolbar: PropertyRef = PropertyRef(
        "visibility_auto_submit_toolbar",
        description="Okta visibility auto submit toolbar.",
    )
    visibility_hide: PropertyRef = PropertyRef(
        "visibility_hide", description="Okta visibility hide."
    )


@dataclass(frozen=True)
class OktaApplicationToOktaOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this resource.",
    )


@dataclass(frozen=True)
# (:OktaApplication)<-[:RESOURCE]-(:OktaOrganization)
class OktaApplicationToOktaOrganizationRelPropertiesRel(CartographyRelSchema):
    target_node_label: str = "OktaOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef(
                "OKTA_ORG_ID",
                set_in_kwargs=True,
                description="Identifier of the owning Okta organization.",
            )
        },
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: OktaApplicationToOktaOrganizationRelProperties = (
        OktaApplicationToOktaOrganizationRelProperties()
    )


@dataclass(frozen=True)
class OktaApplicationToOktaUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this resource.",
    )


@dataclass(frozen=True)
class OktaApplicationToOktaUserPropertiesRel(CartographyRelSchema):
    # (:OktaApplication)<-[:APPLICATION]-(:OktaUser)
    target_node_label: str = "OktaUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef(
                "user_id", description="Identifier of the related Okta user."
            )
        },
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "APPLICATION"
    properties: OktaApplicationToOktaUserRelProperties = (
        OktaApplicationToOktaUserRelProperties()
    )


@dataclass(frozen=True)
class OktaApplicationToOktaGroupRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this resource.",
    )


@dataclass(frozen=True)
class OktaApplicationToOktaGroupPropertiesRel(CartographyRelSchema):
    # (:OktaApplication)<-[:APPLICATION]-(:OktaGroup)
    target_node_label: str = "OktaGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef(
                "group_id", description="Identifier of the related Okta group."
            )
        },
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "APPLICATION"
    properties: OktaApplicationToOktaGroupRelProperties = (
        OktaApplicationToOktaGroupRelProperties()
    )


@dataclass(frozen=True)
class OktaApplicationSchema(CartographyNodeSchema):
    label: str = "OktaApplication"
    properties: OktaApplicationNodeProperties = OktaApplicationNodeProperties()
    sub_resource_relationship: OktaApplicationToOktaOrganizationRelPropertiesRel = (
        OktaApplicationToOktaOrganizationRelPropertiesRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        rels=[
            OktaApplicationToOktaUserPropertiesRel(),
            OktaApplicationToOktaGroupPropertiesRel(),
        ],
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([THIRD_PARTY_APP])


@dataclass(frozen=True)
class OktaApplicationRoleNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description=(
            "Application ID and role assignment ID joined by `:`. Okta's API "
            "reference shows standard role assignment IDs derived from the role "
            "type, so the application ID keeps each app's assignment distinct."
        ),
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this resource.",
    )
    application_id: PropertyRef = PropertyRef(
        "application_id",
        description="ID of the `OktaApplication` the role is assigned to.",
    )
    assignment_id: PropertyRef = PropertyRef(
        "assignment_id", description="Okta ID of the role assignment."
    )
    role_type: PropertyRef = PropertyRef(
        "role_type",
        description=(
            "Okta role type, such as `SUPER_ADMIN`, `READ_ONLY_ADMIN`, or `CUSTOM`."
        ),
    )
    label: PropertyRef = PropertyRef(
        "label", description="Display name of the role, such as `Super Administrator`."
    )
    status: PropertyRef = PropertyRef(
        "status", description="Status of the role assignment, such as `ACTIVE`."
    )
    assignment_type: PropertyRef = PropertyRef(
        "assignment_type",
        description="Type of principal the role is assigned to: `CLIENT` for an app.",
    )
    role_id: PropertyRef = PropertyRef(
        "role_id",
        description=(
            "ID of the custom role, or the role type of an IAM-based standard role. "
            "Null for other standard roles."
        ),
    )
    resource_set_id: PropertyRef = PropertyRef(
        "resource_set_id",
        description=(
            "ID of the resource set that limits a custom or IAM-based role to some "
            "resources. Null for other standard roles."
        ),
    )
    created: PropertyRef = PropertyRef(
        "created", description="When the role was assigned to the app."
    )
    last_updated: PropertyRef = PropertyRef(
        "last_updated", description="When the role assignment was last updated."
    )


@dataclass(frozen=True)
class OktaApplicationRoleToOktaOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this resource.",
    )


@dataclass(frozen=True)
# (:OktaApplicationRole)<-[:RESOURCE]-(:OktaOrganization)
class OktaApplicationRoleToOktaOrganizationRel(CartographyRelSchema):
    """An Okta organization contains an application's admin role assignment."""

    target_node_label: str = "OktaOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef(
                "OKTA_ORG_ID",
                set_in_kwargs=True,
                description="Identifier of the owning Okta organization.",
            )
        },
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: OktaApplicationRoleToOktaOrganizationRelProperties = (
        OktaApplicationRoleToOktaOrganizationRelProperties()
    )


@dataclass(frozen=True)
class OktaApplicationRoleToOktaApplicationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this resource.",
    )


@dataclass(frozen=True)
# (:OktaApplication)-[:HAS_ROLE]->(:OktaApplicationRole)
class OktaApplicationRoleToOktaApplicationRel(CartographyRelSchema):
    """An Okta application holds an admin role."""

    target_node_label: str = "OktaApplication"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef(
                "application_id",
                description="Identifier of the Okta application holding the role.",
            )
        },
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_ROLE"
    properties: OktaApplicationRoleToOktaApplicationRelProperties = (
        OktaApplicationRoleToOktaApplicationRelProperties()
    )


@dataclass(frozen=True)
class OktaApplicationRoleSchema(CartographyNodeSchema):
    """
    An admin role assigned to an Okta app, typically an OAuth service app. The
    role limits which resources the app can reach; its granted scopes
    (`OktaApplication.granted_scopes`) limit which actions it can take.
    """

    label: str = "OktaApplicationRole"
    properties: OktaApplicationRoleNodeProperties = OktaApplicationRoleNodeProperties()
    sub_resource_relationship: OktaApplicationRoleToOktaOrganizationRel = (
        OktaApplicationRoleToOktaOrganizationRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        rels=[
            OktaApplicationRoleToOktaApplicationRel(),
        ],
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([PERMISSION_ROLE])
