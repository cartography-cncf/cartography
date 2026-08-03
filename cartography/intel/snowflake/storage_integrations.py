"""Snowflake storage integrations.

There is no object endpoint for storage integrations, so they come from
``SHOW STORAGE INTEGRATIONS`` plus one ``DESC INTEGRATION`` per integration through
the SQL API. ``DESC`` is what exposes the assumed IAM role, the external id and the
allowed storage locations, which is the whole point of ingesting them: the role is
the bridge between the Snowflake account and the customer's cloud storage.
"""

import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.snowflake.names import name_list
from cartography.intel.snowflake.sql_values import to_bool
from cartography.intel.snowflake.sql_values import to_text
from cartography.intel.snowflake.util import is_sql_unavailable
from cartography.intel.snowflake.util import iso_to_datetime
from cartography.intel.snowflake.util import sf_fqn
from cartography.intel.snowflake.util import sf_id
from cartography.intel.snowflake.util import SnowflakeClient
from cartography.intel.snowflake.util import SnowflakeSqlError
from cartography.intel.snowflake.util import warn_unavailable
from cartography.models.snowflake.storage_integration import (
    SnowflakeStorageIntegrationSchema,
)
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get(client: SnowflakeClient) -> list[dict[str, Any]] | None:
    """Return every storage integration, or None when the SQL surface is unavailable."""
    try:
        return client.run_sql("SHOW STORAGE INTEGRATIONS")
    except SnowflakeSqlError as error:
        if not is_sql_unavailable(error):
            raise
        warn_unavailable(
            "storage integrations", "SHOW STORAGE INTEGRATIONS is not permitted"
        )
        return None


@timeit
def get_details(client: SnowflakeClient, name: str) -> dict[str, str | None] | None:
    """Describe one storage integration, or None when it cannot be described."""
    try:
        return client.describe(f"DESC INTEGRATION {sf_fqn(name)}")
    except SnowflakeSqlError as error:
        if not is_sql_unavailable(error):
            raise
        warn_unavailable(
            f"storage integration {name}", "DESC INTEGRATION is not permitted"
        )
        return None


def transform(
    integrations: list[dict[str, Any]],
    details_by_name: dict[str, dict[str, str | None]],
    account_id: str,
) -> list[dict[str, Any]]:
    transformed: list[dict[str, Any]] = []
    for integration in integrations:
        name = integration["name"]
        details = details_by_name.get(name, {})
        transformed.append(
            {
                "id": sf_id(account_id, "storage_integration", sf_fqn(name)),
                "name": name,
                "integration_type": to_text(integration.get("type")),
                "category": to_text(integration.get("category")),
                # SHOW reports enabled for every integration; DESC repeats it, so
                # prefer SHOW and fall back to DESC.
                "enabled": (
                    to_bool(integration.get("enabled"))
                    if integration.get("enabled") not in (None, "")
                    else to_bool(details.get("enabled"))
                ),
                "storage_provider": to_text(details.get("storage_provider")),
                "storage_allowed_locations": name_list(
                    details.get("storage_allowed_locations")
                ),
                "storage_blocked_locations": name_list(
                    details.get("storage_blocked_locations")
                ),
                "storage_aws_role_arn": to_text(details.get("storage_aws_role_arn")),
                "storage_aws_iam_user_arn": to_text(
                    details.get("storage_aws_iam_user_arn")
                ),
                "storage_aws_external_id": to_text(
                    details.get("storage_aws_external_id")
                ),
                "azure_tenant_id": to_text(details.get("azure_tenant_id")),
                "azure_multi_tenant_app_name": to_text(
                    details.get("azure_multi_tenant_app_name")
                ),
                "use_privatelink_endpoint": to_bool(
                    details.get("use_privatelink_endpoint")
                ),
                "comment": to_text(integration.get("comment")),
                "created_on": iso_to_datetime(integration.get("created_on")),
            },
        )
    return transformed


def load_storage_integrations(
    neo4j_session: neo4j.Session,
    integrations: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        SnowflakeStorageIntegrationSchema(),
        integrations,
        lastupdated=update_tag,
        ACCOUNT_ID=account_id,
    )


def cleanup(neo4j_session: neo4j.Session, common_job_parameters: dict) -> None:
    GraphJob.from_node_schema(
        SnowflakeStorageIntegrationSchema(), common_job_parameters
    ).run(neo4j_session)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: SnowflakeClient,
    common_job_parameters: dict,
) -> bool:
    """Sync Snowflake storage integrations.

    Runs before stages so a stage's USES_INTEGRATION edge resolves against an
    integration node already in the graph.

    Returns whether every integration could be listed and described. When one could
    not, the caller skips cleanup rather than deleting integrations it merely failed
    to re-read.
    """
    integrations = get(client)
    if integrations is None:
        return False

    details_by_name: dict[str, dict[str, str | None]] = {}
    complete = True
    for integration in integrations:
        name = integration["name"]
        details = get_details(client, name)
        if details is None:
            complete = False
            continue
        details_by_name[name] = details

    # Only load the integrations whose DESCRIBE succeeded. An integration listed by
    # SHOW but not describable has none of its interesting properties, and loading it
    # anyway would overwrite the values a previous run collected with nulls. Skipping
    # cleanup is not enough on its own, because load() still rewrites the node.
    describable = [
        integration
        for integration in integrations
        if integration["name"] in details_by_name
    ]
    transformed = transform(describable, details_by_name, client.account_id)
    logger.info(
        "Loading %d Snowflake storage integrations for account %s.",
        len(transformed),
        client.account_id,
    )
    load_storage_integrations(
        neo4j_session,
        transformed,
        client.account_id,
        common_job_parameters["UPDATE_TAG"],
    )
    return complete
