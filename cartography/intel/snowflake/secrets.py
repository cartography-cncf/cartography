"""Snowflake secrets: the schema-level credentials external access code reads.

Secrets are listed per schema. Snowflake never returns secret material through the API
and this module never stores any either: only the metadata that says what the credential
is, who owns it and when it expires.
"""

import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.snowflake.util import iso_to_datetime
from cartography.intel.snowflake.util import sf_fqn
from cartography.intel.snowflake.util import sf_id
from cartography.intel.snowflake.util import sf_path_segment
from cartography.intel.snowflake.util import skip_or_raise_http
from cartography.intel.snowflake.util import SnowflakeClient
from cartography.models.snowflake.secret import SnowflakeSecretSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_schema_secrets(
    client: SnowflakeClient,
    database_name: str,
    schema_name: str,
) -> list[dict[str, Any]] | None:
    """Secrets of one schema, or None when the role cannot read that schema."""
    try:
        return client.list_all(
            f"/api/v2/databases/{sf_path_segment(database_name)}/schemas/{sf_path_segment(schema_name)}/secrets",
        )
    except requests.HTTPError as error:
        skip_or_raise_http(error, 403, 404)
        logger.warning(
            "Cannot list secrets of Snowflake schema %s.%s (permission denied); they "
            "will be missing from the graph.",
            database_name,
            schema_name,
        )
        return None


@timeit
def get(
    client: SnowflakeClient, schemas: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], bool]:
    """Return every readable secret plus whether every schema could be read."""
    secrets: list[dict[str, Any]] = []
    complete = True
    for schema in schemas:
        rows = get_schema_secrets(client, schema["database_name"], schema["name"])
        if rows is None:
            complete = False
            continue
        secrets.extend(rows)
    return secrets, complete


def transform(secrets: list[dict[str, Any]], account_id: str) -> list[dict[str, Any]]:
    transformed: list[dict[str, Any]] = []
    for secret in secrets:
        database_name = secret["database_name"]
        schema_name = secret["schema_name"]
        name = secret["name"]
        qualified_name = sf_fqn(database_name, schema_name, name)
        api_authentication = secret.get("api_authentication") or None
        transformed.append(
            {
                "id": sf_id(account_id, "secret", qualified_name),
                "name": name,
                "qualified_name": qualified_name,
                "database_name": database_name,
                "schema_name": schema_name,
                "parent_schema_id": sf_id(
                    account_id, "schema", sf_fqn(database_name, schema_name)
                ),
                # Snowflake spells this `secret_type` on some API versions and `type`
                # on others; both name the kind of credential held.
                "secret_type": secret.get("secret_type") or secret.get("type"),
                "username": secret.get("username"),
                "oauth_scopes": secret.get("oauth_scopes"),
                "oauth_refresh_token_expiry_time": iso_to_datetime(
                    secret.get("oauth_refresh_token_expiry_time"),
                ),
                "api_authentication": api_authentication,
                # Null when the secret is not OAuth-backed, which suppresses the edge
                # rather than pointing it at a nonexistent node.
                "api_authentication_id": (
                    sf_id(
                        account_id,
                        "security_integration",
                        sf_fqn(api_authentication),
                    )
                    if api_authentication
                    else None
                ),
                "algorithm": secret.get("algorithm"),
                "key_length": secret.get("key_length"),
                "owner": secret.get("owner"),
                "comment": secret.get("comment"),
                "created_on": iso_to_datetime(secret.get("created_on")),
            },
        )
    return transformed


def load_secrets(
    neo4j_session: neo4j.Session,
    secrets: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        SnowflakeSecretSchema(),
        secrets,
        lastupdated=update_tag,
        ACCOUNT_ID=account_id,
    )


def cleanup(neo4j_session: neo4j.Session, common_job_parameters: dict) -> None:
    GraphJob.from_node_schema(SnowflakeSecretSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: SnowflakeClient,
    schemas: list[dict[str, Any]],
    common_job_parameters: dict,
) -> bool:
    """Sync Snowflake secrets, returning whether every schema could be read.

    Runs after security integrations so the USES_INTEGRATION edge resolves on the first
    pass, and before external access integrations, which point back at these nodes.
    """
    raw_secrets, complete = get(client, schemas)
    secrets = transform(raw_secrets, client.account_id)
    logger.info(
        "Loading %d Snowflake secrets for account %s.", len(secrets), client.account_id
    )
    load_secrets(
        neo4j_session, secrets, client.account_id, common_job_parameters["UPDATE_TAG"]
    )
    if not complete:
        logger.warning(
            "Some Snowflake schemas could not be listed; skipping secret cleanup so "
            "still-valid secrets are not deleted.",
        )
    return complete
