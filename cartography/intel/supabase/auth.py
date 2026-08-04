import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.supabase.util import get_json
from cartography.intel.supabase.util import iso_to_datetime
from cartography.intel.supabase.util import TOLERATED_STATUSES
from cartography.intel.supabase.util import warn_unavailable
from cartography.models.supabase.authconfig import SupabaseAuthConfigSchema
from cartography.models.supabase.ssoprovider import SupabaseSSOProviderSchema
from cartography.models.supabase.thirdpartyauth import (
    SupabaseThirdPartyAuthIntegrationSchema,
)
from cartography.util import timeit

logger = logging.getLogger(__name__)

# The non-secret, security-relevant subset of GET /config/auth. That endpoint
# returns 237 fields including SMTP passwords, the captcha secret, webhook hook
# secrets and test OTPs; anything not named here is never written to the graph.
AUTH_CONFIG_FIELDS = (
    "mfa_totp_enroll_enabled",
    "mfa_totp_verify_enabled",
    "mfa_phone_enroll_enabled",
    "mfa_phone_verify_enabled",
    "mfa_web_authn_enroll_enabled",
    "mfa_web_authn_verify_enabled",
    "mfa_max_enrolled_factors",
    "password_min_length",
    "password_required_characters",
    "password_hibp_enabled",
    "security_update_password_require_reauthentication",
    "security_captcha_enabled",
    "security_captcha_provider",
    "security_manual_linking_enabled",
    "rate_limit_otp",
    "rate_limit_anonymous_users",
    "rate_limit_token_refresh",
    "jwt_exp",
    "refresh_token_rotation_enabled",
    "security_refresh_token_reuse_interval",
    "sessions_timebox",
    "sessions_inactivity_timeout",
    "sessions_single_per_user",
    "disable_signup",
    "external_anonymous_users_enabled",
    "external_email_enabled",
    "external_phone_enabled",
    "mailer_secure_email_change_enabled",
    "mailer_otp_exp",
    "mailer_otp_length",
    "sms_otp_exp",
    "site_url",
    "uri_allow_list",
)

# `external_anonymous_users_enabled` is a sign-up mode rather than a federated
# provider, so it is excluded from the derived provider list.
_NON_PROVIDER_EXTERNAL_FLAGS = frozenset({"external_anonymous_users_enabled"})


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    base_url = common_job_parameters["BASE_URL"]
    project_ref = common_job_parameters["PROJECT_REF"]
    update_tag = common_job_parameters["UPDATE_TAG"]

    auth_config = get(api_session, base_url, project_ref)
    if auth_config is None:
        warn_unavailable("auth configuration", project_ref)
    else:
        load_auth_config(
            neo4j_session,
            transform_auth_config(auth_config, project_ref),
            project_ref,
            update_tag,
        )
        cleanup_auth_config(neo4j_session, common_job_parameters)

    sso_providers = get_sso_providers(api_session, base_url, project_ref)
    if sso_providers is None:
        warn_unavailable("SSO providers", project_ref)
    else:
        load_sso_providers(
            neo4j_session,
            transform_sso_providers(sso_providers),
            project_ref,
            update_tag,
        )
        cleanup_sso_providers(neo4j_session, common_job_parameters)

    third_party = get_third_party_auth(api_session, base_url, project_ref)
    if third_party is None:
        warn_unavailable("third-party auth integrations", project_ref)
    else:
        load_third_party_auth(
            neo4j_session,
            transform_third_party_auth(third_party),
            project_ref,
            update_tag,
        )
        cleanup_third_party_auth(neo4j_session, common_job_parameters)


@timeit
def get(
    api_session: requests.Session,
    base_url: str,
    project_ref: str,
) -> dict[str, Any]:
    return get_json(
        api_session,
        f"{base_url}/v1/projects/{project_ref}/config/auth",
        tolerate=TOLERATED_STATUSES,
    )


@timeit
def get_sso_providers(
    api_session: requests.Session,
    base_url: str,
    project_ref: str,
) -> dict[str, Any]:
    return get_json(
        api_session,
        f"{base_url}/v1/projects/{project_ref}/config/auth/sso/providers",
        tolerate=TOLERATED_STATUSES,
    )


@timeit
def get_third_party_auth(
    api_session: requests.Session,
    base_url: str,
    project_ref: str,
) -> list[dict[str, Any]]:
    return get_json(
        api_session,
        f"{base_url}/v1/projects/{project_ref}/config/auth/third-party-auth",
        tolerate=TOLERATED_STATUSES,
    )


def transform_auth_config(
    auth_config: dict[str, Any] | None,
    project_ref: str,
) -> list[dict[str, Any]]:
    if not auth_config:
        return []

    record: dict[str, Any] = {"id": f"{project_ref}/auth"}
    for field in AUTH_CONFIG_FIELDS:
        record[field] = auth_config.get(field)

    record["enabled_external_providers"] = sorted(
        key[len("external_") : -len("_enabled")]
        for key, value in auth_config.items()
        if key.startswith("external_")
        and key.endswith("_enabled")
        and key not in _NON_PROVIDER_EXTERNAL_FLAGS
        and value
    )
    return [record]


def transform_sso_providers(
    sso_providers: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for provider in (sso_providers or {}).get("items") or []:
        saml = provider.get("saml") or {}
        result.append(
            {
                "id": provider["id"],
                "entity_id": saml.get("entity_id"),
                "metadata_url": saml.get("metadata_url"),
                "name_id_format": saml.get("name_id_format"),
                "domains": [
                    d["domain"]
                    for d in provider.get("domains") or []
                    if d.get("domain")
                ],
                "created_at": iso_to_datetime(provider.get("created_at")),
                "updated_at": iso_to_datetime(provider.get("updated_at")),
            },
        )
    return result


def transform_third_party_auth(
    integrations: list[dict[str, Any]] | None,
) -> list[dict[str, Any]]:
    return [
        {
            "id": integration["id"],
            "type": integration.get("type"),
            "oidc_issuer_url": integration.get("oidc_issuer_url"),
            "jwks_url": integration.get("jwks_url"),
            "inserted_at": iso_to_datetime(integration.get("inserted_at")),
            "updated_at": iso_to_datetime(integration.get("updated_at")),
            "resolved_at": iso_to_datetime(integration.get("resolved_at")),
        }
        for integration in integrations or []
    ]


@timeit
def load_auth_config(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    project_ref: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        SupabaseAuthConfigSchema(),
        data,
        lastupdated=update_tag,
        PROJECT_REF=project_ref,
    )


@timeit
def load_sso_providers(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    project_ref: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        SupabaseSSOProviderSchema(),
        data,
        lastupdated=update_tag,
        PROJECT_REF=project_ref,
    )


@timeit
def load_third_party_auth(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    project_ref: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        SupabaseThirdPartyAuthIntegrationSchema(),
        data,
        lastupdated=update_tag,
        PROJECT_REF=project_ref,
    )


@timeit
def cleanup_auth_config(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(SupabaseAuthConfigSchema(), common_job_parameters).run(
        neo4j_session,
    )


@timeit
def cleanup_sso_providers(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(SupabaseSSOProviderSchema(), common_job_parameters).run(
        neo4j_session,
    )


@timeit
def cleanup_third_party_auth(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(
        SupabaseThirdPartyAuthIntegrationSchema(),
        common_job_parameters,
    ).run(neo4j_session)
