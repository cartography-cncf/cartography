"""Snowflake password policies.

``SHOW PASSWORD POLICIES IN ACCOUNT`` lists the policies but not what they require;
the requirements only come from ``DESCRIBE PASSWORD POLICY``. A policy whose
settings could not be described is skipped rather than loaded with every requirement
nulled out, because a null minimum length reads as "no requirement" and would
misreport the account's posture.
"""

import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.snowflake.sql_values import describe_policy
from cartography.intel.snowflake.sql_values import to_int
from cartography.intel.snowflake.sql_values import to_text
from cartography.intel.snowflake.util import is_sql_unavailable
from cartography.intel.snowflake.util import iso_to_datetime
from cartography.intel.snowflake.util import sf_fqn
from cartography.intel.snowflake.util import sf_id
from cartography.intel.snowflake.util import SnowflakeClient
from cartography.intel.snowflake.util import SnowflakeSqlError
from cartography.intel.snowflake.util import warn_unavailable
from cartography.models.snowflake.password_policy import SnowflakePasswordPolicySchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

_SETTING_KEYS = (
    "password_min_length",
    "password_max_length",
    "password_min_upper_case_chars",
    "password_min_lower_case_chars",
    "password_min_numeric_chars",
    "password_min_special_chars",
    "password_min_age_days",
    "password_max_age_days",
    "password_max_retries",
    "password_lockout_time_mins",
    "password_history",
)


@timeit
def get(client: SnowflakeClient) -> list[dict[str, Any]] | None:
    """Every password policy with its described settings, or None when unreadable.

    Each returned row is the listing row plus a ``settings`` mapping.
    """
    try:
        policies = client.run_sql("SHOW PASSWORD POLICIES IN ACCOUNT")
    except SnowflakeSqlError as error:
        if not is_sql_unavailable(error):
            raise
        warn_unavailable(
            "password policies", "SHOW PASSWORD POLICIES IN ACCOUNT is not permitted"
        )
        return None

    described: list[dict[str, Any]] = []
    for policy in policies:
        qualified_name = sf_fqn(
            policy["database_name"], policy["schema_name"], policy["name"]
        )
        settings = describe_policy(
            client,
            f"DESC PASSWORD POLICY {qualified_name}",
            f"password policy {qualified_name}",
        )
        if settings is None:
            # Describing a policy needs ownership or APPLY on it, so one refusal
            # means the collector's view is incomplete. Give up on the whole surface
            # rather than returning a subset that cleanup would then converge to.
            return None
        described.append({**policy, "settings": settings})
    return described


def transform(
    policies: list[dict[str, Any]],
    account_id: str,
) -> list[dict[str, Any]]:
    """Shape listing rows plus described settings into nodes."""
    transformed: list[dict[str, Any]] = []

    for policy in policies:
        database_name = policy["database_name"]
        schema_name = policy["schema_name"]
        name = policy["name"]
        qualified_name = sf_fqn(database_name, schema_name, name)
        settings = policy["settings"]
        record = {
            "id": sf_id(account_id, "password_policy", qualified_name),
            "name": name,
            "qualified_name": qualified_name,
            "database_name": database_name,
            "schema_name": schema_name,
            "parent_schema_id": sf_id(
                account_id, "schema", sf_fqn(database_name, schema_name)
            ),
            "owner": to_text(policy.get("owner")),
            "owner_role_type": to_text(policy.get("owner_role_type")),
            "comment": to_text(policy.get("comment")),
            "created_on": iso_to_datetime(policy.get("created_on")),
        }
        for key in _SETTING_KEYS:
            record[key] = to_int(settings.get(key))
        transformed.append(record)

    return transformed


def load_password_policies(
    neo4j_session: neo4j.Session,
    policies: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        SnowflakePasswordPolicySchema(),
        policies,
        lastupdated=update_tag,
        ACCOUNT_ID=account_id,
    )


def cleanup(neo4j_session: neo4j.Session, common_job_parameters: dict) -> None:
    GraphJob.from_node_schema(
        SnowflakePasswordPolicySchema(), common_job_parameters
    ).run(neo4j_session)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: SnowflakeClient,
    schemas: list[dict[str, Any]],
    common_job_parameters: dict,
) -> bool:
    """Sync password policies.

    Runs after the schema hierarchy so every containment edge resolves on the first
    pass. ``schemas`` is the already-synced schema listing and is used to report
    policies whose schema is missing from the graph.

    Returns whether the listing could be read. When it could not, the caller skips
    password policy cleanup so previously collected policies are not deleted.
    """
    policies = get(client)
    if policies is None:
        return False

    transformed = transform(policies, client.account_id)
    known_schema_ids = {schema["id"] for schema in schemas}
    unlinked = sum(
        1
        for policy in transformed
        if policy["parent_schema_id"] not in known_schema_ids
    )
    if unlinked:
        logger.warning(
            "%d Snowflake password policies sit in a schema that is not in the graph; "
            "their containment edges are omitted.",
            unlinked,
        )
    logger.info(
        "Loading %d Snowflake password policies for account %s.",
        len(transformed),
        client.account_id,
    )
    load_password_policies(
        neo4j_session,
        transformed,
        client.account_id,
        common_job_parameters["UPDATE_TAG"],
    )
    return True
