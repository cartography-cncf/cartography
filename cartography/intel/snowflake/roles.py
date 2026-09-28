import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.snowflake import account_usage
from cartography.intel.snowflake.util import iso_to_datetime
from cartography.intel.snowflake.util import sf_id
from cartography.intel.snowflake.util import SnowflakeClient
from cartography.models.snowflake.role import SnowflakeRoleSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

# Snowflake creates these roles itself and grants them their privileges. Telling
# them apart from customer-defined roles matters because they are the roles an
# attack path is trying to reach.
BUILTIN_ROLES = frozenset(
    {
        "ORGADMIN",
        "ACCOUNTADMIN",
        "SECURITYADMIN",
        "USERADMIN",
        "SYSADMIN",
        "PUBLIC",
    },
)


def role_type_of(name: str) -> str:
    return "BUILTIN" if name.upper() in BUILTIN_ROLES else "CUSTOM"


@timeit
def get(client: SnowflakeClient) -> list[dict[str, Any]]:
    return client.list_all("/api/v2/roles")


def transform(roles: list[dict[str, Any]], account_id: str) -> list[dict[str, Any]]:
    transformed: list[dict[str, Any]] = []
    for role in roles:
        name = role["name"]
        transformed.append(
            {
                "id": sf_id(account_id, "role", name),
                "name": name,
                "role_type": role_type_of(name),
                "comment": role.get("comment"),
                # Snowflake reports no owner for the roles it created itself.
                "owner": role.get("owner") or None,
                "assigned_to_users": role.get("assigned_to_users"),
                "granted_to_roles": role.get("granted_to_roles"),
                "granted_roles": role.get("granted_roles"),
                "created_on": iso_to_datetime(role.get("created_on")),
            },
        )
    return transformed


def load_roles(
    neo4j_session: neo4j.Session,
    roles: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        SnowflakeRoleSchema(),
        roles,
        lastupdated=update_tag,
        ACCOUNT_ID=account_id,
    )


def cleanup(neo4j_session: neo4j.Session, common_job_parameters: dict) -> None:
    GraphJob.from_node_schema(SnowflakeRoleSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: SnowflakeClient,
    account_usage_roles: list[dict[str, Any]] | None,
    common_job_parameters: dict,
) -> tuple[list[dict[str, Any]], bool]:
    """Sync Snowflake account roles and return them for the grant syncs to walk.

    Runs early: users, the role hierarchy and every grant edge resolve against
    role nodes, and the grant syncs need the role list to know what to enumerate.

    Returns ``(roles, complete)``. ``complete`` is only True on the ACCOUNT_USAGE
    path, because ``/api/v2/roles`` follows ``SHOW ROLES`` visibility: without
    ``MANAGE GRANTS`` it returns a successful but partial list, indistinguishable
    from a full one. Reporting that as complete is what would let cleanup delete
    roles the collector simply could not see, so the REST path reports incomplete
    and the caller skips role cleanup.
    """
    if account_usage_roles is not None:
        raw_roles, _ = account_usage.split_roles(account_usage_roles)
        complete = True
        logger.info(
            "Reading Snowflake roles from ACCOUNT_USAGE, which is account-wide.",
        )
    else:
        raw_roles = get(client)
        complete = False
        logger.warning(
            "Reading Snowflake roles from the object API, which only returns roles "
            "visible to the collector role. Completeness cannot be established, so "
            "role cleanup will be skipped. Grant IMPORTED PRIVILEGES ON DATABASE "
            "SNOWFLAKE to read the account-wide ACCOUNT_USAGE views instead.",
        )

    roles = transform(raw_roles, client.account_id)
    logger.info(
        "Loading %d Snowflake roles for account %s.", len(roles), client.account_id
    )
    load_roles(
        neo4j_session, roles, client.account_id, common_job_parameters["UPDATE_TAG"]
    )
    return roles, complete
