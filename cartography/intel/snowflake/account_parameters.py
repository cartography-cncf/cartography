"""Snowflake account parameters.

``SHOW PARAMETERS IN ACCOUNT`` returns several hundred rows, the large majority of
which are performance or ergonomics knobs. Only the parameters that decide a
security outcome are loaded as nodes; the rest would bury those few facts.

This module also resolves the account-level ``NETWORK_POLICY`` value, because that
parameter is the only place Snowflake states which network policy is in force
account-wide. The network policy sync uses it to attach the policy to the account.
"""

import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.snowflake.sql_values import to_text
from cartography.intel.snowflake.util import is_sql_unavailable
from cartography.intel.snowflake.util import sf_fqn
from cartography.intel.snowflake.util import sf_id
from cartography.intel.snowflake.util import SnowflakeClient
from cartography.intel.snowflake.util import SnowflakeSqlError
from cartography.intel.snowflake.util import warn_unavailable
from cartography.models.snowflake.account_parameter import (
    SnowflakeAccountParameterSchema,
)
from cartography.util import timeit

logger = logging.getLogger(__name__)

NETWORK_POLICY_PARAMETER = "NETWORK_POLICY"

# The account parameters whose value changes the account's security posture. Every
# other parameter Snowflake reports is deliberately not loaded.
SECURITY_PARAMETERS = frozenset(
    {
        NETWORK_POLICY_PARAMETER,
        "ALLOW_CLIENT_MFA_CACHING",
        "ALLOW_ID_TOKEN",
        "DATA_RETENTION_TIME_IN_DAYS",
        "ENABLE_INTERNAL_STAGES_PRIVATELINK",
        "ENABLE_UNREDACTED_QUERY_SYNTAX_ERROR",
        "ENFORCE_NETWORK_RULES_FOR_INTERNAL_STAGES",
        "MIN_DATA_RETENTION_TIME_IN_DAYS",
        "OAUTH_ADD_PRIVILEGED_ROLES_TO_BLOCKED_LIST",
        "PERIODIC_DATA_REKEYING",
        "PREVENT_LOAD_FROM_INLINE_URL",
        "PREVENT_UNLOAD_TO_INLINE_URL",
        "PREVENT_UNLOAD_TO_INTERNAL_STAGES",
        "REQUIRE_STORAGE_INTEGRATION_FOR_STAGE_CREATION",
        "REQUIRE_STORAGE_INTEGRATION_FOR_STAGE_OPERATION",
        "SAML_IDENTITY_PROVIDER",
        "SSO_LOGIN_PAGE",
    }
)


@timeit
def get(client: SnowflakeClient) -> list[dict[str, Any]] | None:
    """Every account parameter, or None when not permitted."""
    try:
        return client.run_sql("SHOW PARAMETERS IN ACCOUNT")
    except SnowflakeSqlError as error:
        if not is_sql_unavailable(error):
            raise
        warn_unavailable(
            "account parameters", "SHOW PARAMETERS IN ACCOUNT is not permitted"
        )
        return None


@timeit
def get_account_network_policy(client: SnowflakeClient) -> str | None:
    """The network policy in force account-wide, or None when unset or unreadable.

    Uses the narrower filtered statement rather than the full parameter listing so
    that an account whose full listing is too large or is refused can still have its
    account-level policy attached.
    """
    try:
        rows = client.run_sql(
            f"SHOW PARAMETERS LIKE '%{NETWORK_POLICY_PARAMETER}%' IN ACCOUNT"
        )
    except SnowflakeSqlError as error:
        if not is_sql_unavailable(error):
            raise
        warn_unavailable(
            "account network policy", "SHOW PARAMETERS IN ACCOUNT is not permitted"
        )
        return None

    for row in rows:
        if to_text(row.get("key")) == NETWORK_POLICY_PARAMETER:
            return to_text(row.get("value"))
    return None


def transform(
    parameters: list[dict[str, Any]],
    account_id: str,
) -> list[dict[str, Any]]:
    """Keep the security-relevant parameters and shape them into nodes."""
    transformed: list[dict[str, Any]] = []

    for parameter in parameters:
        key = parameter["key"]
        if key.upper() not in SECURITY_PARAMETERS:
            continue
        value = to_text(parameter.get("value"))
        default_value = to_text(parameter.get("default"))
        transformed.append(
            {
                "id": sf_id(account_id, "account_parameter", sf_fqn(key)),
                "name": key,
                "value": value,
                "default_value": default_value,
                "is_default": value == default_value,
                "level": to_text(parameter.get("level")),
                "parameter_type": to_text(parameter.get("type")),
                "description": to_text(parameter.get("description")),
            },
        )

    return transformed


def load_account_parameters(
    neo4j_session: neo4j.Session,
    parameters: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        SnowflakeAccountParameterSchema(),
        parameters,
        lastupdated=update_tag,
        ACCOUNT_ID=account_id,
    )


def cleanup(neo4j_session: neo4j.Session, common_job_parameters: dict) -> None:
    GraphJob.from_node_schema(
        SnowflakeAccountParameterSchema(), common_job_parameters
    ).run(neo4j_session)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: SnowflakeClient,
    common_job_parameters: dict,
) -> tuple[str | None, bool]:
    """Sync the security-relevant account parameters.

    Returns the account-level network policy name and whether the parameter listing
    could be read. The caller passes the policy name to the network policy sync and,
    when the listing could not be read, skips parameter cleanup so previously
    collected parameters are not deleted.
    """
    network_policy = get_account_network_policy(client)
    parameters = get(client)
    if parameters is None:
        return network_policy, False

    transformed = transform(parameters, client.account_id)
    logger.info(
        "Loading %d security-relevant Snowflake account parameters for account %s.",
        len(transformed),
        client.account_id,
    )
    load_account_parameters(
        neo4j_session,
        transformed,
        client.account_id,
        common_job_parameters["UPDATE_TAG"],
    )
    return network_policy, True
