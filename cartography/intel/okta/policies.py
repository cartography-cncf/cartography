from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

import neo4j
from okta.client import Client as OktaClient

from cartography.client.core.tx import load
from cartography.client.core.tx import read_list_of_values_tx
from cartography.graph.job import GraphJob
from cartography.intel.okta.common import collect_raw_paginated
from cartography.intel.okta.common import get_raw_json
from cartography.intel.okta.common import is_missing_scope_error
from cartography.intel.okta.common import is_resource_not_found_error
from cartography.intel.okta.common import OktaApiError
from cartography.models.okta.policy import OktaPolicyRuleSchema
from cartography.models.okta.policy import OktaPolicySchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

# Policy types that carry the settings security baselines inspect. The last two
# exist only in Okta Identity Engine orgs.
POLICY_TYPES = (
    "OKTA_SIGN_ON",
    "PASSWORD",
    "MFA_ENROLL",
    "ACCESS_POLICY",
    "PROFILE_ENROLLMENT",
)
IDENTITY_ENGINE_POLICY_TYPES = {"ACCESS_POLICY", "PROFILE_ENROLLMENT"}
# Okta rejects an unknown policy type with an API validation error.
OKTA_VALIDATION_ERROR_CODE = "E0000001"


def _json(value: Any) -> str | None:
    return json.dumps(value) if value is not None else None


def _include_exclude(condition: dict[str, Any] | None) -> tuple[list, list]:
    condition = condition or {}
    return condition.get("include") or [], condition.get("exclude") or []


def _app_id_from_mapping(mapping: dict[str, Any]) -> str | None:
    href = (mapping.get("_links") or {}).get("application", {}).get("href")
    return href.rstrip("/").rsplit("/", 1)[-1] if href else None


@timeit
async def _get_okta_policies(okta_client: OktaClient) -> list[dict[str, Any]]:
    policies: list[dict[str, Any]] = []
    for policy_type in POLICY_TYPES:
        try:
            policies.extend(
                await collect_raw_paginated(
                    okta_client,
                    "/api/v1/policies",
                    {"type": policy_type},
                ),
            )
        except OktaApiError as exc:
            if (
                policy_type in IDENTITY_ENGINE_POLICY_TYPES
                and exc.error_code == OKTA_VALIDATION_ERROR_CODE
            ):
                logger.info(
                    "Okta org does not support %s policies (Classic Engine); skipping",
                    policy_type,
                )
                continue
            raise
    return policies


@timeit
async def _get_okta_policy_rules(
    okta_client: OktaClient,
    policy_id: str,
) -> list[dict[str, Any]] | None:
    try:
        return await collect_raw_paginated(
            okta_client,
            f"/api/v1/policies/{policy_id}/rules",
        )
    except OktaApiError as exc:
        # The policy was deleted after the list call; None tells the caller to drop it.
        if is_resource_not_found_error(exc):
            return None
        raise


@timeit
async def _get_okta_policy_app_ids(
    okta_client: OktaClient,
    policy_id: str,
) -> list[str] | None:
    try:
        mappings = await collect_raw_paginated(
            okta_client,
            f"/api/v1/policies/{policy_id}/mappings",
        )
    except OktaApiError as exc:
        if is_resource_not_found_error(exc):
            return None
        raise
    return [
        app_id for app_id in map(_app_id_from_mapping, mappings) if app_id is not None
    ]


@timeit
async def _get_okta_first_party_app_names(
    okta_client: OktaClient,
    app_ids: set[str],
) -> dict[str, str]:
    """Resolve the name of apps the Applications API does not list."""
    names: dict[str, str] = {}
    for app_id in sorted(app_ids):
        try:
            app = await get_raw_json(okta_client, f"/api/v1/apps/{app_id}")
        except OktaApiError as exc:
            if is_resource_not_found_error(exc):
                continue
            raise
        if app and app.get("name"):
            names[app_id] = app["name"]
    return names


@timeit
async def _get_okta_policy_data(
    okta_client: OktaClient,
    known_app_ids: set[str],
) -> tuple[
    list[dict[str, Any]],
    dict[str, list[dict[str, Any]]],
    dict[str, list[str]],
    dict[str, str],
]:
    policies: list[dict[str, Any]] = []
    rules_by_policy: dict[str, list[dict[str, Any]]] = {}
    app_ids_by_policy: dict[str, list[str]] = {}
    for policy in await _get_okta_policies(okta_client):
        policy_id = policy["id"]
        rules = await _get_okta_policy_rules(okta_client, policy_id)
        if rules is None:
            logger.info("Okta policy %s was deleted during sync; skipping", policy_id)
            continue
        if policy.get("type") == "ACCESS_POLICY":
            app_ids = await _get_okta_policy_app_ids(okta_client, policy_id)
            if app_ids is None:
                logger.info(
                    "Okta policy %s was deleted during sync; skipping",
                    policy_id,
                )
                continue
            app_ids_by_policy[policy_id] = app_ids
        policies.append(policy)
        rules_by_policy[policy_id] = rules
    unknown_app_ids = {
        app_id
        for app_ids in app_ids_by_policy.values()
        for app_id in app_ids
        if app_id not in known_app_ids
    }
    first_party_app_names = await _get_okta_first_party_app_names(
        okta_client,
        unknown_app_ids,
    )
    return policies, rules_by_policy, app_ids_by_policy, first_party_app_names


def _get_known_app_ids(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> set[str]:
    return {
        str(app_id)
        for app_id in neo4j_session.execute_read(
            read_list_of_values_tx,
            """
            MATCH (:OktaOrganization {id: $OKTA_ORG_ID})-[:RESOURCE]->(app:OktaApplication)
            RETURN app.id
            """,
            OKTA_ORG_ID=common_job_parameters["OKTA_ORG_ID"],
        )
    }


def _transform_okta_policies(
    policies: list[dict[str, Any]],
    app_ids_by_policy: dict[str, list[str]],
    first_party_app_names: dict[str, str],
) -> list[dict[str, Any]]:
    transformed: list[dict[str, Any]] = []
    for policy in policies:
        conditions = policy.get("conditions") or {}
        settings = policy.get("settings") or {}
        groups_include, groups_exclude = _include_exclude(
            (conditions.get("people") or {}).get("groups"),
        )
        password = settings.get("password") or {}
        complexity = password.get("complexity") or {}
        age = password.get("age") or {}
        lockout = password.get("lockout") or {}
        authenticators = settings.get("authenticators") or []
        app_ids = app_ids_by_policy.get(policy["id"], [])

        def _enrollment(state: str) -> list[str]:
            return [
                authenticator["key"]
                for authenticator in authenticators
                if (authenticator.get("enroll") or {}).get("self") == state
            ]

        transformed.append(
            {
                "id": policy["id"],
                "name": policy.get("name"),
                "description": policy.get("description"),
                "type": policy.get("type"),
                "status": policy.get("status"),
                "priority": policy.get("priority"),
                "system": policy.get("system"),
                "created": policy.get("created"),
                "okta_last_updated": policy.get("lastUpdated"),
                "group_include_ids": groups_include,
                "group_exclude_ids": groups_exclude,
                "auth_provider": (conditions.get("authProvider") or {}).get("provider"),
                "application_ids": app_ids,
                "first_party_app_names": sorted(
                    first_party_app_names[app_id]
                    for app_id in app_ids
                    if app_id in first_party_app_names
                ),
                "password_min_length": complexity.get("minLength"),
                "password_min_lowercase": complexity.get("minLowerCase"),
                "password_min_uppercase": complexity.get("minUpperCase"),
                "password_min_number": complexity.get("minNumber"),
                "password_min_symbol": complexity.get("minSymbol"),
                "password_exclude_username": complexity.get("excludeUsername"),
                "password_exclude_attributes": complexity.get("excludeAttributes"),
                "password_common_password_check": (
                    (complexity.get("dictionary") or {}).get("common") or {}
                ).get("exclude"),
                "password_max_age_days": age.get("maxAgeDays"),
                "password_expire_warn_days": age.get("expireWarnDays"),
                "password_min_age_minutes": age.get("minAgeMinutes"),
                "password_history_count": age.get("historyCount"),
                "lockout_max_attempts": lockout.get("maxAttempts"),
                "lockout_auto_unlock_minutes": lockout.get("autoUnlockMinutes"),
                "lockout_show_failures": lockout.get("showLockoutFailures"),
                "lockout_notification_channels": lockout.get(
                    "userLockoutNotificationChannels"
                ),
                "enrollment_required_authenticators": _enrollment("REQUIRED"),
                "enrollment_optional_authenticators": _enrollment("OPTIONAL"),
                "enrollment_disabled_authenticators": _enrollment("NOT_ALLOWED"),
                "conditions": _json(policy.get("conditions")),
                "settings": _json(policy.get("settings")),
            },
        )
    return transformed


def _all_constraints_require(
    constraints: list[dict[str, Any]],
    possession_field: str,
) -> bool:
    return bool(constraints) and all(
        (constraint.get("possession") or {}).get(possession_field) == "REQUIRED"
        for constraint in constraints
    )


def _transform_okta_policy_rules(
    rules_by_policy: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    transformed: list[dict[str, Any]] = []
    for policy_id, rules in rules_by_policy.items():
        for rule in rules:
            conditions = rule.get("conditions") or {}
            actions = rule.get("actions") or {}
            people = conditions.get("people") or {}
            users_include, users_exclude = _include_exclude(people.get("users"))
            groups_include, groups_exclude = _include_exclude(people.get("groups"))
            network = conditions.get("network") or {}
            zones_include, zones_exclude = _include_exclude(network)

            signon = actions.get("signon") or {}
            session = signon.get("session") or {}
            app_sign_on = actions.get("appSignOn") or {}
            verification = app_sign_on.get("verificationMethod") or {}
            constraints = verification.get("constraints") or []
            profile_enrollment = actions.get("profileEnrollment") or {}

            transformed.append(
                {
                    "id": rule["id"],
                    "policy_id": policy_id,
                    "name": rule.get("name"),
                    "type": rule.get("type"),
                    "status": rule.get("status"),
                    "priority": rule.get("priority"),
                    "system": rule.get("system"),
                    "created": rule.get("created"),
                    "okta_last_updated": rule.get("lastUpdated"),
                    "user_include_ids": users_include,
                    "user_exclude_ids": users_exclude,
                    "group_include_ids": groups_include,
                    "group_exclude_ids": groups_exclude,
                    "network_connection": network.get("connection"),
                    "network_include_zone_ids": zones_include,
                    "network_exclude_zone_ids": zones_exclude,
                    "risk_score_level": (conditions.get("riskScore") or {}).get(
                        "level"
                    ),
                    "access": (
                        signon.get("access")
                        or app_sign_on.get("access")
                        or profile_enrollment.get("access")
                    ),
                    "require_factor": signon.get("requireFactor"),
                    "primary_factor": signon.get("primaryFactor"),
                    "factor_prompt_mode": signon.get("factorPromptMode"),
                    "factor_lifetime_minutes": signon.get("factorLifetime"),
                    "remember_device_by_default": signon.get("rememberDeviceByDefault"),
                    "session_max_idle_minutes": session.get("maxSessionIdleMinutes"),
                    "session_max_lifetime_minutes": session.get(
                        "maxSessionLifetimeMinutes"
                    ),
                    "session_use_persistent_cookie": session.get("usePersistentCookie"),
                    "factor_mode": verification.get("factorMode"),
                    "verification_method_type": verification.get("type"),
                    "reauthenticate_in": verification.get("reauthenticateIn"),
                    "phishing_resistant_required": (
                        _all_constraints_require(constraints, "phishingResistant")
                        if verification
                        else None
                    ),
                    "hardware_protection_required": (
                        _all_constraints_require(constraints, "hardwareProtection")
                        if verification
                        else None
                    ),
                    "device_bound_required": (
                        _all_constraints_require(constraints, "deviceBound")
                        if verification
                        else None
                    ),
                    "verification_constraints": (
                        _json(constraints) if verification else None
                    ),
                    "enroll_self": (actions.get("enroll") or {}).get("self"),
                    "password_change_access": (actions.get("passwordChange") or {}).get(
                        "access"
                    ),
                    "self_service_password_reset_access": (
                        actions.get("selfServicePasswordReset") or {}
                    ).get("access"),
                    "self_service_unlock_access": (
                        actions.get("selfServiceUnlock") or {}
                    ).get("access"),
                    "conditions": _json(rule.get("conditions")),
                    "actions": _json(rule.get("actions")),
                },
            )
    return transformed


def _load_okta_policies(
    neo4j_session: neo4j.Session,
    policies: list[dict[str, Any]],
    common_job_parameters: dict[str, Any],
) -> None:
    load(
        neo4j_session,
        OktaPolicySchema(),
        policies,
        lastupdated=common_job_parameters["UPDATE_TAG"],
        OKTA_ORG_ID=common_job_parameters["OKTA_ORG_ID"],
    )


def _load_okta_policy_rules(
    neo4j_session: neo4j.Session,
    rules: list[dict[str, Any]],
    common_job_parameters: dict[str, Any],
) -> None:
    load(
        neo4j_session,
        OktaPolicyRuleSchema(),
        rules,
        lastupdated=common_job_parameters["UPDATE_TAG"],
        OKTA_ORG_ID=common_job_parameters["OKTA_ORG_ID"],
    )


def _cleanup_okta_policies(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(
        OktaPolicyRuleSchema(),
        common_job_parameters,
    ).run(neo4j_session)
    GraphJob.from_node_schema(
        OktaPolicySchema(),
        common_job_parameters,
    ).run(neo4j_session)


@timeit
def sync_okta_policies(
    okta_client: OktaClient,
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Sync Okta global session, password, authentication, authenticator
    enrollment, and profile enrollment policies with their rules.

    Run after the application sync: authentication policies are linked to the
    `OktaApplication` nodes it loads.
    """
    logger.info("Syncing Okta policies")
    known_app_ids = _get_known_app_ids(neo4j_session, common_job_parameters)
    try:
        policies, rules_by_policy, app_ids_by_policy, first_party_app_names = (
            asyncio.run(_get_okta_policy_data(okta_client, known_app_ids))
        )
    except OktaApiError as exc:
        # Policy listing requires okta.policies.read. Existing tokens often lack
        # it; skip this sub-sync so the rest of Okta ingestion still runs.
        if is_missing_scope_error(exc):
            logger.warning(
                "Unable to sync Okta policies - api token needs okta.policies.read",
            )
            return
        raise

    transformed_policies = _transform_okta_policies(
        policies,
        app_ids_by_policy,
        first_party_app_names,
    )
    transformed_rules = _transform_okta_policy_rules(rules_by_policy)
    _load_okta_policies(neo4j_session, transformed_policies, common_job_parameters)
    _load_okta_policy_rules(neo4j_session, transformed_rules, common_job_parameters)
    _cleanup_okta_policies(neo4j_session, common_job_parameters)
    logger.info(
        "Loaded %s Okta policies and %s policy rules",
        len(transformed_policies),
        len(transformed_rules),
    )
