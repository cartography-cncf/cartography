"""Snowflake stored procedures.

A procedure carries everything a function does plus ``execute_as``, which decides
whether the body runs with the owner's privileges or the caller's. That single
field is what turns a procedure into a privilege-escalation stepping stone, so it
drives an explicit edge to the owning role.
"""

import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.snowflake.names import external_access_integration_ids
from cartography.intel.snowflake.names import name_list
from cartography.intel.snowflake.names import normalize_signature
from cartography.intel.snowflake.names import routine_qualified_name
from cartography.intel.snowflake.names import secret_ids
from cartography.intel.snowflake.names import secret_references
from cartography.intel.snowflake.util import datatype_of
from cartography.intel.snowflake.util import iso_to_datetime
from cartography.intel.snowflake.util import sf_id
from cartography.intel.snowflake.util import sf_path_segment
from cartography.intel.snowflake.util import skip_or_raise_http
from cartography.intel.snowflake.util import SnowflakeClient
from cartography.models.snowflake.procedure import SnowflakeProcedureSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get(
    client: SnowflakeClient,
    database_name: str,
    schema_name: str,
) -> list[dict[str, Any]] | None:
    """Stored procedures in one schema, or None when the schema is not readable."""
    try:
        return client.list_all(
            f"/api/v2/databases/{sf_path_segment(database_name)}/schemas/{sf_path_segment(schema_name)}/procedures",
        )
    except requests.HTTPError as error:
        skip_or_raise_http(error, 403, 404)
        return None


def transform(
    procedures: list[dict[str, Any]],
    schema: dict[str, Any],
    account_id: str,
) -> list[dict[str, Any]]:
    database_name = schema["database_name"]
    schema_name = schema["name"]
    transformed: list[dict[str, Any]] = []

    for procedure in procedures:
        name = procedure["name"]
        # The object API calls the argument list `signature`; the SQL API renders
        # the same information as `arguments`.
        signature = normalize_signature(
            procedure.get("signature") or procedure.get("arguments"),
        )
        qualified_name = routine_qualified_name(
            database_name, schema_name, name, signature
        )
        owner = procedure.get("owner")
        # A caller-rights procedure runs with the caller's own privileges, so there
        # is no single role to point at and the edge is suppressed. A procedure owned
        # by a database role is suppressed too: that owner is a SnowflakeDatabaseRole,
        # so resolving it as an account role would point ASSUMES at the wrong
        # principal type or at nothing at all.
        owner_role_id = (
            sf_id(account_id, "role", owner)
            if owner
            and procedure.get("execute_as") == "OWNER"
            and procedure.get("owner_role_type") != "DATABASE_ROLE"
            else None
        )
        transformed.append(
            {
                "id": sf_id(account_id, "procedure", qualified_name),
                "name": name,
                "qualified_name": qualified_name,
                "database_name": database_name,
                "schema_name": schema_name,
                "parent_schema_id": schema["id"],
                "signature": signature,
                "returns": procedure.get("returns")
                or datatype_of(procedure.get("return_type")),
                "language": procedure.get("language"),
                "execute_as": procedure.get("execute_as"),
                "is_secure": procedure.get("is_secure"),
                "is_external_function": procedure.get("is_external_function"),
                "is_memoizable": procedure.get("is_memoizable"),
                "is_builtin": procedure.get("is_builtin"),
                "api_integration": procedure.get("api_integration"),
                "handler": procedure.get("handler"),
                "runtime_version": procedure.get("runtime_version"),
                "packages": name_list(procedure.get("packages")),
                "imports": name_list(procedure.get("imports")),
                "external_access_integrations": name_list(
                    procedure.get("external_access_integrations"),
                ),
                "external_access_integration_ids": external_access_integration_ids(
                    procedure.get("external_access_integrations"),
                    account_id,
                ),
                "secrets": secret_references(procedure.get("secrets")),
                "secret_ids": secret_ids(
                    procedure.get("secrets"), database_name, schema_name, account_id
                ),
                "owner": owner,
                "owner_role_id": owner_role_id,
                "comment": procedure.get("comment"),
                "created_on": iso_to_datetime(procedure.get("created_on")),
            },
        )
    return transformed


def load_procedures(
    neo4j_session: neo4j.Session,
    procedures: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        SnowflakeProcedureSchema(),
        procedures,
        lastupdated=update_tag,
        ACCOUNT_ID=account_id,
    )


def cleanup(neo4j_session: neo4j.Session, common_job_parameters: dict) -> None:
    GraphJob.from_node_schema(SnowflakeProcedureSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: SnowflakeClient,
    schemas: list[dict[str, Any]],
    common_job_parameters: dict,
) -> bool:
    """Sync every stored procedure in every readable schema.

    Returns whether the walk was complete, so the caller can skip procedure
    cleanup rather than deleting nodes it merely failed to re-read this run.
    """
    account_id = client.account_id
    procedures: list[dict[str, Any]] = []
    complete = True

    for schema in schemas:
        listing = get(client, schema["database_name"], schema["name"])
        if listing is None:
            complete = False
            continue
        procedures.extend(transform(listing, schema, account_id))

    logger.info(
        "Loading %d Snowflake stored procedures for account %s.",
        len(procedures),
        account_id,
    )
    load_procedures(
        neo4j_session, procedures, account_id, common_job_parameters["UPDATE_TAG"]
    )

    if not complete:
        logger.warning(
            "Some Snowflake schemas could not be read for stored procedures; "
            "skipping procedure cleanup so still-valid nodes are not deleted.",
        )
    return complete
