"""Snowflake user-defined functions.

Snowflake lists functions through two endpoints: ``functions`` covers every
function visible in the schema, including the built-ins, while
``user-defined-functions`` covers only the ones the account defined. Both are
walked and merged, because which of the two an account exposes varies and a
function present in only one of them would otherwise be missed.
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
from cartography.intel.snowflake.util import sf_fqn
from cartography.intel.snowflake.util import sf_id
from cartography.intel.snowflake.util import sf_path_segment
from cartography.intel.snowflake.util import skip_or_raise_http
from cartography.intel.snowflake.util import SnowflakeClient
from cartography.models.snowflake.function import SnowflakeFunctionSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

_FUNCTION_ENDPOINTS = ("functions", "user-defined-functions")


@timeit
def get(
    client: SnowflakeClient,
    database_name: str,
    schema_name: str,
) -> list[dict[str, Any]] | None:
    """Functions in one schema, or None when neither listing is readable."""
    functions: list[dict[str, Any]] = []
    readable = False
    for endpoint in _FUNCTION_ENDPOINTS:
        try:
            functions.extend(
                client.list_all(
                    f"/api/v2/databases/{sf_path_segment(database_name)}/schemas/{sf_path_segment(schema_name)}/{endpoint}",
                ),
            )
        except requests.HTTPError as error:
            skip_or_raise_http(error, 403, 404)
            continue
        readable = True
    return functions if readable else None


def transform(
    functions: list[dict[str, Any]],
    schema: dict[str, Any],
    account_id: str,
) -> list[dict[str, Any]]:
    """Build function nodes, keyed on name plus normalised argument types.

    The two listings overlap, so the same overload can arrive twice; the id is
    what identifies it, and the later copy simply replaces the earlier one.
    """
    database_name = schema["database_name"]
    schema_name = schema["name"]
    transformed: dict[str, dict[str, Any]] = {}

    for function in functions:
        name = function["name"]
        # The object API calls the argument list `signature`; the SQL API renders
        # the same information as `arguments`.
        signature = normalize_signature(
            function.get("signature") or function.get("arguments"),
        )
        qualified_name = routine_qualified_name(
            database_name, schema_name, name, signature
        )
        api_integration = function.get("api_integration")
        node_id = sf_id(account_id, "function", qualified_name)
        transformed[node_id] = {
            "id": node_id,
            "name": name,
            "qualified_name": qualified_name,
            "database_name": database_name,
            "schema_name": schema_name,
            "parent_schema_id": schema["id"],
            "signature": signature,
            "returns": function.get("returns")
            or datatype_of(function.get("return_type")),
            "language": function.get("language"),
            "is_secure": function.get("is_secure"),
            "is_external_function": function.get("is_external_function"),
            "is_memoizable": function.get("is_memoizable"),
            "is_builtin": function.get("is_builtin"),
            "api_integration": api_integration,
            "api_integration_id": (
                sf_id(account_id, "api_integration", sf_fqn(api_integration))
                if api_integration
                else None
            ),
            "handler": function.get("handler"),
            "runtime_version": function.get("runtime_version"),
            "packages": name_list(function.get("packages")),
            "imports": name_list(function.get("imports")),
            "external_access_integrations": name_list(
                function.get("external_access_integrations"),
            ),
            "external_access_integration_ids": external_access_integration_ids(
                function.get("external_access_integrations"),
                account_id,
            ),
            "secrets": secret_references(function.get("secrets")),
            "secret_ids": secret_ids(
                function.get("secrets"), database_name, schema_name, account_id
            ),
            "owner": function.get("owner"),
            "comment": function.get("comment"),
            "created_on": iso_to_datetime(function.get("created_on")),
        }
    return list(transformed.values())


def load_functions(
    neo4j_session: neo4j.Session,
    functions: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        SnowflakeFunctionSchema(),
        functions,
        lastupdated=update_tag,
        ACCOUNT_ID=account_id,
    )


def cleanup(neo4j_session: neo4j.Session, common_job_parameters: dict) -> None:
    GraphJob.from_node_schema(SnowflakeFunctionSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: SnowflakeClient,
    schemas: list[dict[str, Any]],
    common_job_parameters: dict,
) -> bool:
    """Sync every function in every readable schema.

    Returns whether the walk was complete, so the caller can skip function
    cleanup rather than deleting nodes it merely failed to re-read this run.
    """
    account_id = client.account_id
    functions: list[dict[str, Any]] = []
    complete = True

    for schema in schemas:
        listing = get(client, schema["database_name"], schema["name"])
        if listing is None:
            complete = False
            continue
        functions.extend(transform(listing, schema, account_id))

    logger.info(
        "Loading %d Snowflake functions for account %s.",
        len(functions),
        account_id,
    )
    load_functions(
        neo4j_session, functions, account_id, common_job_parameters["UPDATE_TAG"]
    )

    if not complete:
        logger.warning(
            "Some Snowflake schemas could not be read for functions; skipping "
            "function cleanup so still-valid nodes are not deleted.",
        )
    return complete
