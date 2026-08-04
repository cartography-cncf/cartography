# GET /v1/projects/{ref}/config/auth. The real response carries 237 fields; this
# fixture keeps the curated subset the module ingests plus a few of the secret and
# irrelevant fields it must drop.
SUPABASE_AUTH_CONFIG = {
    "mfa_totp_enroll_enabled": True,
    "mfa_totp_verify_enabled": True,
    "mfa_phone_enroll_enabled": False,
    "mfa_phone_verify_enabled": False,
    "mfa_web_authn_enroll_enabled": False,
    "mfa_web_authn_verify_enabled": False,
    "mfa_max_enrolled_factors": 10,
    "password_min_length": 8,
    "password_required_characters": "abcdefghijklmnopqrstuvwxyz:ABCDEFGHIJKLMNOPQRSTUVWXYZ",
    "password_hibp_enabled": False,
    "security_update_password_require_reauthentication": True,
    "security_captcha_enabled": True,
    "security_captcha_provider": "hcaptcha",
    "security_manual_linking_enabled": False,
    "rate_limit_otp": 30,
    "rate_limit_anonymous_users": 30,
    "rate_limit_token_refresh": 150,
    "jwt_exp": 3600,
    "refresh_token_rotation_enabled": True,
    "security_refresh_token_reuse_interval": 10,
    "sessions_timebox": 0,
    "sessions_inactivity_timeout": 0,
    "sessions_single_per_user": False,
    "disable_signup": False,
    "external_anonymous_users_enabled": False,
    "external_email_enabled": True,
    "external_phone_enabled": False,
    "external_github_enabled": True,
    "external_google_enabled": True,
    "external_apple_enabled": False,
    "external_slack_oidc_enabled": False,
    "mailer_secure_email_change_enabled": True,
    "mailer_otp_exp": 3600,
    "mailer_otp_length": 6,
    "sms_otp_exp": 60,
    "site_url": "https://plant.simpson.corp",
    "uri_allow_list": "https://plant.simpson.corp/**",
    # Secret and irrelevant fields that must never be ingested.
    "security_captcha_secret": "hcaptcha-secret-do-not-ingest",
    "smtp_pass": "smtp-password-do-not-ingest",
    "sms_test_otp": "123456",
    "hook_mfa_verification_attempt_secrets": "v1,whsec_do-not-ingest",
    "mailer_subjects_invite": "You have been invited",
}

# GET /v1/projects/{ref}/config/auth/sso/providers
SUPABASE_SSO_PROVIDERS = {
    "items": [
        {
            "id": "sso-provider-1",
            "saml": {
                "entity_id": "https://idp.simpson.corp/saml/metadata",
                "metadata_url": "https://idp.simpson.corp/saml/metadata.xml",
                "metadata_xml": "<EntityDescriptor/>",
                "attribute_mapping": {"keys": {}},
                "name_id_format": "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress",
            },
            "domains": [
                {
                    "domain": "simpson.corp",
                    "created_at": "2026-07-08T10:00:00Z",
                    "updated_at": "2026-07-08T10:00:00Z",
                },
                {
                    "domain": "springfield.simpson.corp",
                    "created_at": "2026-07-08T10:00:00Z",
                    "updated_at": "2026-07-08T10:00:00Z",
                },
            ],
            "created_at": "2026-07-08T10:00:00Z",
            "updated_at": "2026-07-09T10:00:00Z",
        },
    ],
}

# GET /v1/projects/{ref}/config/auth/third-party-auth
SUPABASE_THIRD_PARTY_AUTH = [
    {
        "id": "tpa-firebase-1",
        "type": "firebase",
        "oidc_issuer_url": "https://securetoken.google.com/simpson-corp",
        "jwks_url": "https://www.googleapis.com/service_accounts/v1/jwk/securetoken@system.gserviceaccount.com",
        "custom_jwks": None,
        "resolved_jwks": None,
        "inserted_at": "2026-07-11T10:00:00Z",
        "updated_at": "2026-07-11T10:00:00Z",
        "resolved_at": "2026-07-27T10:00:00Z",
    },
]
