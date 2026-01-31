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
class OktaApplicationNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    accessibility_error_redirect_url: PropertyRef = PropertyRef(
        "accessibility_error_redirect_url"
    )

    accessibility_login_redirect_url: PropertyRef = PropertyRef(
        "accessibility_login_redirect_url"
    )
    accessibility_self_service: PropertyRef = PropertyRef("accessibility_self_service")
    created: PropertyRef = PropertyRef("created")
    credentials_signing_kid: PropertyRef = PropertyRef("credentials_signing_kid")
    credentials_signing_last_rotated: PropertyRef = PropertyRef(
        "credentials_signing_last_rotated"
    )
    credentials_signing_next_rotation: PropertyRef = PropertyRef(
        "credentials_signing_next_rotation"
    )
    credentials_signing_rotation_mode: PropertyRef = PropertyRef(
        "credentials_signing_rotation_mode"
    )
    credentials_signing_use: PropertyRef = PropertyRef("credentials_signing_use")
    credentials_user_name_template_push_status: PropertyRef = PropertyRef(
        "credentials_user_name_template_push_status"
    )
    credentials_user_name_template_suffix: PropertyRef = PropertyRef(
        "credentials_user_name_template_suffix"
    )
    credentials_user_name_template_template: PropertyRef = PropertyRef(
        "credentials_user_name_template_template"
    )
    credentials_user_name_template_type: PropertyRef = PropertyRef(
        "credentials_user_name_template_type"
    )
    features: PropertyRef = PropertyRef("features")
    label: PropertyRef = PropertyRef("label")
    last_updated: PropertyRef = PropertyRef("last_updated")
    licensing_seat_count: PropertyRef = PropertyRef("licensing_seat_count")
    name: PropertyRef = PropertyRef("name")
    settings_app_acs_url: PropertyRef = PropertyRef("settings_app_acs_url")
    settings_app_button_field: PropertyRef = PropertyRef("settings_app_button_field")
    settings_app_login_url_regex: PropertyRef = PropertyRef(
        "settings_app_login_url_regex"
    )
    settings_app_org_name: PropertyRef = PropertyRef("settings_app_org_name")
    settings_app_password_field: PropertyRef = PropertyRef(
        "settings_app_password_field"
    )
    settings_app_url: PropertyRef = PropertyRef("settings_app_url")
    settings_app_username_field: PropertyRef = PropertyRef(
        "settings_app_username_field"
    )
    settings_app_implicit_assignment: PropertyRef = PropertyRef(
        "settings_app_implicit_assignment"
    )
    settings_app_inline_hook_id: PropertyRef = PropertyRef(
        "settings_app_inline_hook_id"
    )
    settings_notifications_vpn_help_url: PropertyRef = PropertyRef(
        "settings_notifications_vpn_help_url"
    )
    settings_notifications_vpn_message: PropertyRef = PropertyRef(
        "settings_notifications_vpn_message"
    )
    settings_notifications_vpn_network_connection: PropertyRef = PropertyRef(
        "settings_notifications_vpn_network_connection"
    )
    settings_notifications_vpn_network_exclude: PropertyRef = PropertyRef(
        "settings_notifications_vpn_network_exclude"
    )
    settings_notifications_vpn_network_include: PropertyRef = PropertyRef(
        "settings_notifications_vpn_network_include"
    )
    settings_notes_admin: PropertyRef = PropertyRef("settings_notes_admin")
    settings_notes_enduser: PropertyRef = PropertyRef("settings_notes_enduser")
    settings_oauth_client_application_type: PropertyRef = PropertyRef(
        "settings_oauth_client_application_type"
    )
    settings_oauth_client_client_uri: PropertyRef = PropertyRef(
        "settings_oauth_client_client_uri"
    )
    settings_oauth_client_consent_method: PropertyRef = PropertyRef(
        "settings_oauth_client_consent_method"
    )
    settings_oauth_client_grant_Type: PropertyRef = PropertyRef(
        "settings_oauth_client_grant_Type"
    )
    settings_oauth_client_idp_initiated_login_default_scope: PropertyRef = PropertyRef(
        "settings_oauth_client_idp_initiated_login_default_scope"
    )
    settings_oauth_client_idp_initiated_login_mode: PropertyRef = PropertyRef(
        "settings_oauth_client_idp_initiated_login_mode"
    )
    settings_oauth_client_initiate_login_uri: PropertyRef = PropertyRef(
        "settings_oauth_client_initiate_login_uri"
    )
    settings_oauth_client_logo_uri: PropertyRef = PropertyRef(
        "settings_oauth_client_logo_uri"
    )
    settings_oauth_client_policy_uri: PropertyRef = PropertyRef(
        "settings_oauth_client_policy_uri"
    )
    settings_oauth_client_post_logout_redirect_uris: PropertyRef = PropertyRef(
        "settings_oauth_client_post_logout_redirect_uris"
    )
    settings_oauth_client_redirect_uris: PropertyRef = PropertyRef(
        "settings_oauth_client_redirect_uris"
    )
    settings_oauth_client_response_types: PropertyRef = PropertyRef(
        "settings_oauth_client_response_types"
    )
    settings_oauth_client_tos_uri: PropertyRef = PropertyRef(
        "settings_oauth_client_tos_uri"
    )
    settings_oauth_client_wildcard_redirect: PropertyRef = PropertyRef(
        "settings_oauth_client_wildcard_redirect"
    )
    # SAML sign-on configuration properties
    settings_sign_on_default_relay_state: PropertyRef = PropertyRef(
        "settings_sign_on_default_relay_state"
    )
    settings_sign_on_sso_acs_url: PropertyRef = PropertyRef(
        "settings_sign_on_sso_acs_url"
    )
    settings_sign_on_sso_acs_url_override: PropertyRef = PropertyRef(
        "settings_sign_on_sso_acs_url_override"
    )
    settings_sign_on_recipient: PropertyRef = PropertyRef("settings_sign_on_recipient")
    settings_sign_on_recipient_override: PropertyRef = PropertyRef(
        "settings_sign_on_recipient_override"
    )
    settings_sign_on_destination: PropertyRef = PropertyRef(
        "settings_sign_on_destination"
    )
    settings_sign_on_destination_override: PropertyRef = PropertyRef(
        "settings_sign_on_destination_override"
    )
    settings_sign_on_audience: PropertyRef = PropertyRef("settings_sign_on_audience")
    settings_sign_on_audience_override: PropertyRef = PropertyRef(
        "settings_sign_on_audience_override"
    )
    settings_sign_on_idp_issuer: PropertyRef = PropertyRef(
        "settings_sign_on_idp_issuer"
    )
    settings_sign_on_subject_name_id_template: PropertyRef = PropertyRef(
        "settings_sign_on_subject_name_id_template"
    )
    settings_sign_on_subject_name_id_format: PropertyRef = PropertyRef(
        "settings_sign_on_subject_name_id_format"
    )
    settings_sign_on_response_signed: PropertyRef = PropertyRef(
        "settings_sign_on_response_signed"
    )
    settings_sign_on_assertion_signed: PropertyRef = PropertyRef(
        "settings_sign_on_assertion_signed"
    )
    settings_sign_on_signature_algorithm: PropertyRef = PropertyRef(
        "settings_sign_on_signature_algorithm"
    )
    settings_sign_on_digest_algorithm: PropertyRef = PropertyRef(
        "settings_sign_on_digest_algorithm"
    )
    settings_sign_on_honor_force_authn: PropertyRef = PropertyRef(
        "settings_sign_on_honor_force_authn"
    )
    settings_sign_on_authn_context_class_ref: PropertyRef = PropertyRef(
        "settings_sign_on_authn_context_class_ref"
    )
    sign_on_mode: PropertyRef = PropertyRef("sign_on_mode")
    status: PropertyRef = PropertyRef("status")
    visibility_app_links: PropertyRef = PropertyRef("visibility_app_links")
    visibility_auto_launch: PropertyRef = PropertyRef("visibility_auto_launch")
    visibility_auto_submit_toolbar: PropertyRef = PropertyRef(
        "visibility_auto_submit_toolbar"
    )
    visibility_hide: PropertyRef = PropertyRef("visibility_hide")


@dataclass(frozen=True)
class OktaApplicationToOktaOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:OktaApplication)<-[:RESOURCE]-(:OktaOrganization)
class OktaApplicationToOktaOrganizationRelPropertiesRel(CartographyRelSchema):
    target_node_label: str = "OktaOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("OKTA_ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: OktaApplicationToOktaOrganizationRelProperties = (
        OktaApplicationToOktaOrganizationRelProperties()
    )


@dataclass(frozen=True)
class OktaApplicationToOktaUserProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class OktaApplicationToOktaUserPropertiesRel(CartographyRelSchema):
    # (:OktaApplication)<-[:IS_ASSIGNED_APP]-(:OktaUser)
    target_node_label: str = "OktaUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("user_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "IS_ASSIGNED_APP"
    properties: OktaApplicationToOktaUserProperties = (
        OktaApplicationToOktaUserProperties()
    )


@dataclass(frozen=True)
class OktaApplicationToOktaGroupProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class OktaApplicationToOktaGroupPropertiesRel(CartographyRelSchema):
    # (:OktaApplication)<-[:IS_ASSIGNED_APP]-(:OktaUser)
    target_node_label: str = "OktaGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("group_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "IS_ASSIGNED_APP"
    properties: OktaApplicationToOktaGroupProperties = (
        OktaApplicationToOktaGroupProperties()
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
