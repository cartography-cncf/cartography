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
class SupabaseAuthConfigNodeProperties(CartographyNodeProperties):
    """
    A curated subset of GET /v1/projects/{ref}/config/auth.

    That endpoint returns 237 fields, including SMTP passwords, the captcha secret,
    webhook hook secrets and test OTPs. Only the non-secret security-relevant
    settings below are ingested.
    """

    # Synthesised as "<project ref>/auth": the config is a singleton per project.
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)

    # Multi-factor authentication.
    mfa_totp_enroll_enabled: PropertyRef = PropertyRef("mfa_totp_enroll_enabled")
    mfa_totp_verify_enabled: PropertyRef = PropertyRef("mfa_totp_verify_enabled")
    mfa_phone_enroll_enabled: PropertyRef = PropertyRef("mfa_phone_enroll_enabled")
    mfa_phone_verify_enabled: PropertyRef = PropertyRef("mfa_phone_verify_enabled")
    mfa_web_authn_enroll_enabled: PropertyRef = PropertyRef(
        "mfa_web_authn_enroll_enabled",
    )
    mfa_web_authn_verify_enabled: PropertyRef = PropertyRef(
        "mfa_web_authn_verify_enabled",
    )
    mfa_max_enrolled_factors: PropertyRef = PropertyRef("mfa_max_enrolled_factors")

    # Password policy.
    password_min_length: PropertyRef = PropertyRef("password_min_length")
    password_required_characters: PropertyRef = PropertyRef(
        "password_required_characters",
    )
    password_hibp_enabled: PropertyRef = PropertyRef("password_hibp_enabled")
    security_update_password_require_reauthentication: PropertyRef = PropertyRef(
        "security_update_password_require_reauthentication",
    )

    # Abuse prevention.
    security_captcha_enabled: PropertyRef = PropertyRef("security_captcha_enabled")
    security_captcha_provider: PropertyRef = PropertyRef("security_captcha_provider")
    security_manual_linking_enabled: PropertyRef = PropertyRef(
        "security_manual_linking_enabled",
    )
    rate_limit_otp: PropertyRef = PropertyRef("rate_limit_otp")
    rate_limit_anonymous_users: PropertyRef = PropertyRef("rate_limit_anonymous_users")
    rate_limit_token_refresh: PropertyRef = PropertyRef("rate_limit_token_refresh")

    # Tokens and sessions.
    jwt_exp: PropertyRef = PropertyRef("jwt_exp")
    refresh_token_rotation_enabled: PropertyRef = PropertyRef(
        "refresh_token_rotation_enabled",
    )
    security_refresh_token_reuse_interval: PropertyRef = PropertyRef(
        "security_refresh_token_reuse_interval",
    )
    sessions_timebox: PropertyRef = PropertyRef("sessions_timebox")
    sessions_inactivity_timeout: PropertyRef = PropertyRef(
        "sessions_inactivity_timeout",
    )
    sessions_single_per_user: PropertyRef = PropertyRef("sessions_single_per_user")

    # Sign-up surface.
    disable_signup: PropertyRef = PropertyRef("disable_signup")
    external_anonymous_users_enabled: PropertyRef = PropertyRef(
        "external_anonymous_users_enabled",
    )
    external_email_enabled: PropertyRef = PropertyRef("external_email_enabled")
    external_phone_enabled: PropertyRef = PropertyRef("external_phone_enabled")
    # Derived in transform: the names of every enabled external_*_enabled provider.
    enabled_external_providers: PropertyRef = PropertyRef(
        "enabled_external_providers",
    )

    # Email and OTP handling.
    mailer_secure_email_change_enabled: PropertyRef = PropertyRef(
        "mailer_secure_email_change_enabled",
    )
    mailer_otp_exp: PropertyRef = PropertyRef("mailer_otp_exp")
    mailer_otp_length: PropertyRef = PropertyRef("mailer_otp_length")
    sms_otp_exp: PropertyRef = PropertyRef("sms_otp_exp")

    # Redirect allowlist.
    site_url: PropertyRef = PropertyRef("site_url")
    uri_allow_list: PropertyRef = PropertyRef("uri_allow_list")


@dataclass(frozen=True)
class SupabaseAuthConfigToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SupabaseProject)-[:RESOURCE]->(:SupabaseAuthConfig)
class SupabaseAuthConfigToProjectRel(CartographyRelSchema):
    target_node_label: str = "SupabaseProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_REF", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SupabaseAuthConfigToProjectRelProperties = (
        SupabaseAuthConfigToProjectRelProperties()
    )


@dataclass(frozen=True)
class SupabaseAuthConfigSchema(CartographyNodeSchema):
    label: str = "SupabaseAuthConfig"
    properties: SupabaseAuthConfigNodeProperties = SupabaseAuthConfigNodeProperties()
    sub_resource_relationship: SupabaseAuthConfigToProjectRel = (
        SupabaseAuthConfigToProjectRel()
    )
