import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.snowflake import account_usage
from cartography.intel.snowflake.util import iso_to_datetime
from cartography.intel.snowflake.util import sf_fqn
from cartography.intel.snowflake.util import sf_id
from cartography.intel.snowflake.util import sf_path_segment
from cartography.intel.snowflake.util import skip_or_raise_http
from cartography.intel.snowflake.util import SnowflakeClient
from cartography.models.snowflake.role import SnowflakeDatabaseRoleSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get(
    client: SnowflakeClient,
    databases: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], bool]:
    """List database roles for every readable database.

    Database roles are enumerated per database, so a role without ``USAGE`` on one
    database sees a 403 there. That is skipped rather than failing the sync, and
    the returned completeness flag tells the caller not to run cleanup.
    """
    results: list[dict[str, Any]] = []
    complete = True
    for database in databases:
        database_name = database["name"]
        try:
            roles = client.list_all(
                f"/api/v2/databases/{sf_path_segment(database_name)}/database-roles",
            )
        except requests.HTTPError as error:
            skip_or_raise_http(error, 403, 404)
            logger.info(
                "Skipping Snowflake database roles for database %s: not authorized.",
                database_name,
            )
            complete = False
            continue
        for role in roles:
            results.append({**role, "database_name": database_name})
    return results, complete


def transform(
    database_roles: list[dict[str, Any]],
    account_id: str,
) -> list[dict[str, Any]]:
    transformed: list[dict[str, Any]] = []
    for role in database_roles:
        name = role["name"]
        database_name = role["database_name"]
        qualified_name = sf_fqn(database_name, name)
        transformed.append(
            {
                "id": sf_id(account_id, "database_role", qualified_name),
                "name": name,
                "qualified_name": qualified_name,
                "database_name": database_name,
                "parent_database_id": sf_id(
                    account_id, "database", sf_fqn(database_name)
                ),
                "comment": role.get("comment"),
                "owner": role.get("owner") or None,
                "granted_to_roles": role.get("granted_to_roles"),
                "granted_to_database_roles": role.get("granted_to_database_roles"),
                "granted_database_roles": role.get("granted_database_roles"),
                "created_on": iso_to_datetime(role.get("created_on")),
            },
        )
    return transformed


def load_database_roles(
    neo4j_session: neo4j.Session,
    database_roles: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        SnowflakeDatabaseRoleSchema(),
        database_roles,
        lastupdated=update_tag,
        ACCOUNT_ID=account_id,
    )


def cleanup(neo4j_session: neo4j.Session, common_job_parameters: dict) -> None:
    GraphJob.from_node_schema(SnowflakeDatabaseRoleSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: SnowflakeClient,
    databases: list[dict[str, Any]],
    account_usage_roles: list[dict[str, Any]] | None,
    common_job_parameters: dict,
) -> tuple[list[dict[str, Any]], bool]:
    """Sync database roles and return them so the grant sync can resolve hierarchy.

    Runs after databases (the CONTAINS edge needs the database node) and before
    grants, which needs the qualified names to tell a database role apart from an
    account role in ``grants-of`` output.

    ACCOUNT_USAGE covers every database at once, including the ones this sync does
    not walk, so it is both complete and cheaper than one request per database.
    """
    if account_usage_roles is not None:
        _, raw = account_usage.split_roles(account_usage_roles)
        complete = True
    else:
        raw, complete = get(client, databases)
    database_roles = transform(raw, client.account_id)
    logger.info(
        "Loading %d Snowflake database roles for account %s.",
        len(database_roles),
        client.account_id,
    )
    load_database_roles(
        neo4j_session,
        database_roles,
        client.account_id,
        common_job_parameters["UPDATE_TAG"],
    )
    return database_roles, complete
