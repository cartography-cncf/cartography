"""Snowflake catalog integrations.

The ``catalog`` sub-object holds the Glue coordinates and the Iceberg REST catalog
configuration and is flattened onto the node. The REST catalog's OAuth *client
secret* is deliberately never carried onto the node; only the client id is, so an
operator can tell which application the catalog is accessed as.
"""

import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.snowflake.util import iso_to_datetime
from cartography.intel.snowflake.util import sf_fqn
from cartography.intel.snowflake.util import sf_id
from cartography.intel.snowflake.util import SnowflakeClient
from cartography.models.snowflake.catalog_integration import (
    SnowflakeCatalogIntegrationSchema,
)
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get(client: SnowflakeClient) -> list[dict[str, Any]]:
    return client.list_all("/api/v2/catalog-integrations")


def transform(
    integrations: list[dict[str, Any]],
    account_id: str,
) -> list[dict[str, Any]]:
    transformed: list[dict[str, Any]] = []
    for integration in integrations:
        name = integration["name"]
        catalog = integration.get("catalog") or {}
        rest_config = catalog.get("rest_config") or {}
        rest_authentication = catalog.get("rest_authentication") or {}
        transformed.append(
            {
                "id": sf_id(account_id, "catalog_integration", sf_fqn(name)),
                "name": name,
                "enabled": integration.get("enabled"),
                "integration_type": integration.get("type"),
                "category": integration.get("category"),
                "table_format": integration.get("table_format"),
                "catalog_source": catalog.get("catalog_source"),
                "glue_aws_role_arn": catalog.get("glue_aws_role_arn"),
                "glue_aws_iam_user_arn": catalog.get("glue_aws_iam_user_arn"),
                "glue_catalog_id": catalog.get("glue_catalog_id"),
                "glue_region": catalog.get("glue_region"),
                "catalog_namespace": catalog.get("catalog_namespace"),
                "rest_catalog_uri": rest_config.get("catalog_uri"),
                "rest_warehouse": rest_config.get("warehouse"),
                "rest_authentication_type": rest_authentication.get("type"),
                "oauth_client_id": rest_authentication.get("oauth_client_id"),
                "oauth_allowed_scopes": rest_authentication.get("oauth_allowed_scopes"),
                "comment": integration.get("comment"),
                "created_on": iso_to_datetime(integration.get("created_on")),
            },
        )
    return transformed


def load_catalog_integrations(
    neo4j_session: neo4j.Session,
    integrations: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        SnowflakeCatalogIntegrationSchema(),
        integrations,
        lastupdated=update_tag,
        ACCOUNT_ID=account_id,
    )


def cleanup(neo4j_session: neo4j.Session, common_job_parameters: dict) -> None:
    GraphJob.from_node_schema(
        SnowflakeCatalogIntegrationSchema(), common_job_parameters
    ).run(neo4j_session)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: SnowflakeClient,
    common_job_parameters: dict,
) -> bool:
    """Sync Snowflake catalog integrations."""
    integrations = transform(get(client), client.account_id)
    logger.info(
        "Loading %d Snowflake catalog integrations for account %s.",
        len(integrations),
        client.account_id,
    )
    load_catalog_integrations(
        neo4j_session,
        integrations,
        client.account_id,
        common_job_parameters["UPDATE_TAG"],
    )
    return True
