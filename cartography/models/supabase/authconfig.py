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
    id: PropertyRef = PropertyRef(
        "id", description="Synthesised as `<project ref>/auth`"
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)

    # Multi-factor authentication.
    mfa_totp_enroll_enabled: PropertyRef = PropertyRef(
        "mfa_totp_enroll_enabled", description="Whether users may enrol a TOTP factor"
    )
    mfa_totp_verify_enabled: PropertyRef = PropertyRef(
        "mfa_totp_verify_enabled",
        description="Whether TOTP factors may be used to verify",
    )
    mfa_phone_enroll_enabled: PropertyRef = PropertyRef(
        "mfa_phone_enroll_enabled", description="Whether users may enrol a phone factor"
    )
    mfa_phone_verify_enabled: PropertyRef = PropertyRef(
        "mfa_phone_verify_enabled",
        description="Whether phone factors may be used to verify",
    )
    mfa_web_authn_enroll_enabled: PropertyRef = PropertyRef(
        "mfa_web_authn_enroll_enabled",
        description="Whether users may enrol a WebAuthn factor",
    )
    mfa_web_authn_verify_enabled: PropertyRef = PropertyRef(
        "mfa_web_authn_verify_enabled",
        description="Whether WebAuthn factors may be used to verify",
    )
    mfa_max_enrolled_factors: PropertyRef = PropertyRef(
        "mfa_max_enrolled_factors", description="Maximum factors a user may enrol"
    )

    # Password policy.
    password_min_length: PropertyRef = PropertyRef(
        "password_min_length", description="Minimum password length"
    )
    password_required_characters: PropertyRef = PropertyRef(
        "password_required_characters",
        description="Character classes required in passwords",
    )
    password_hibp_enabled: PropertyRef = PropertyRef(
        "password_hibp_enabled",
        description="Whether passwords are checked against Have I Been Pwned",
    )
    security_update_password_require_reauthentication: PropertyRef = PropertyRef(
        "security_update_password_require_reauthentication",
        description="Whether changing a password requires reauthentication",
    )

    # Abuse prevention.
    security_captcha_enabled: PropertyRef = PropertyRef(
        "security_captcha_enabled", description="Whether captcha protection is enabled"
    )
    security_captcha_provider: PropertyRef = PropertyRef(
        "security_captcha_provider", description="The captcha provider in use"
    )
    security_manual_linking_enabled: PropertyRef = PropertyRef(
        "security_manual_linking_enabled",
        description="Whether users may manually link identities",
    )
    rate_limit_otp: PropertyRef = PropertyRef(
        "rate_limit_otp", description="OTP send rate limit"
    )
    rate_limit_anonymous_users: PropertyRef = PropertyRef(
        "rate_limit_anonymous_users", description="Anonymous sign-in rate limit"
    )
    rate_limit_token_refresh: PropertyRef = PropertyRef(
        "rate_limit_token_refresh", description="Token refresh rate limit"
    )

    # Tokens and sessions.
    jwt_exp: PropertyRef = PropertyRef(
        "jwt_exp", description="Access token lifetime in seconds"
    )
    refresh_token_rotation_enabled: PropertyRef = PropertyRef(
        "refresh_token_rotation_enabled",
        description="Whether refresh tokens rotate on use",
    )
    security_refresh_token_reuse_interval: PropertyRef = PropertyRef(
        "security_refresh_token_reuse_interval",
        description="Grace period for reusing a rotated refresh token",
    )
    sessions_timebox: PropertyRef = PropertyRef(
        "sessions_timebox", description="Maximum absolute session lifetime"
    )
    sessions_inactivity_timeout: PropertyRef = PropertyRef(
        "sessions_inactivity_timeout", description="Session idle timeout"
    )
    sessions_single_per_user: PropertyRef = PropertyRef(
        "sessions_single_per_user",
        description="Whether a user may hold only one session",
    )

    # Sign-up surface.
    disable_signup: PropertyRef = PropertyRef(
        "disable_signup", description="Whether self-service sign-up is disabled"
    )
    external_anonymous_users_enabled: PropertyRef = PropertyRef(
        "external_anonymous_users_enabled",
        description="Whether anonymous sign-ins are allowed",
    )
    external_email_enabled: PropertyRef = PropertyRef(
        "external_email_enabled", description="Whether email sign-in is enabled"
    )
    external_phone_enabled: PropertyRef = PropertyRef(
        "external_phone_enabled", description="Whether phone sign-in is enabled"
    )
    # Derived in transform: the names of every enabled external_*_enabled provider.
    enabled_external_providers: PropertyRef = PropertyRef(
        "enabled_external_providers",
        description="Names of the enabled federated identity providers, derived from the `external_*_enabled` flags",
    )

    # Email and OTP handling.
    mailer_secure_email_change_enabled: PropertyRef = PropertyRef(
        "mailer_secure_email_change_enabled",
        description="Whether email changes require confirmation on both addresses",
    )
    mailer_otp_exp: PropertyRef = PropertyRef(
        "mailer_otp_exp", description="Email OTP lifetime"
    )
    mailer_otp_length: PropertyRef = PropertyRef(
        "mailer_otp_length", description="Email OTP length"
    )
    sms_otp_exp: PropertyRef = PropertyRef(
        "sms_otp_exp", description="SMS OTP lifetime"
    )

    # Redirect allowlist.
    site_url: PropertyRef = PropertyRef(
        "site_url", description="The project's primary site URL"
    )
    uri_allow_list: PropertyRef = PropertyRef(
        "uri_allow_list", description="Allowed post-authentication redirect URIs"
    )


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
    """Represents the authentication configuration of a Supabase project. The API returns 237 fields for this resource; Cartography ingests a curated non-secret subset. SMTP credentials, the captcha secret, webhook hook secrets and test OTPs are never stored."""

    label: str = "SupabaseAuthConfig"
    properties: SupabaseAuthConfigNodeProperties = SupabaseAuthConfigNodeProperties()
    sub_resource_relationship: SupabaseAuthConfigToProjectRel = (
        SupabaseAuthConfigToProjectRel()
    )
