"""Snowflake API integrations.

The ``api_hook`` sub-object holds the provider-specific coordinates (the assumed IAM
role, the Entra ID application, the Google audience) and is flattened onto the node so
the cross-cloud edges can be matched without a nested lookup.
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
from cartography.models.snowflake.api_integration import SnowflakeApiIntegrationSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get(client: SnowflakeClient) -> list[dict[str, Any]]:
    return client.list_all("/api/v2/api-integrations")


def transform(
    integrations: list[dict[str, Any]],
    account_id: str,
) -> list[dict[str, Any]]:
    transformed: list[dict[str, Any]] = []
    for integration in integrations:
        name = integration["name"]
        api_hook = integration.get("api_hook") or {}
        transformed.append(
            {
                "id": sf_id(account_id, "api_integration", sf_fqn(name)),
                "name": name,
                "enabled": integration.get("enabled"),
                "api_allowed_prefixes": integration.get("api_allowed_prefixes"),
                "api_blocked_prefixes": integration.get("api_blocked_prefixes"),
                "api_hook_type": api_hook.get("type"),
                "api_provider": api_hook.get("api_provider"),
                "api_aws_role_arn": api_hook.get("api_aws_role_arn"),
                "api_aws_iam_user_arn": api_hook.get("api_aws_iam_user_arn"),
                "api_aws_external_id": api_hook.get("api_aws_external_id"),
                "azure_tenant_id": api_hook.get("azure_tenant_id"),
                "azure_ad_application_id": api_hook.get("azure_ad_application_id"),
                "google_audience": api_hook.get("google_audience"),
                "allowed_authentication_secrets": api_hook.get(
                    "allowed_authentication_secrets"
                ),
                "allowed_api_authentication_integrations": api_hook.get(
                    "allowed_api_authentication_integrations"
                ),
                "comment": integration.get("comment"),
                "created_on": iso_to_datetime(integration.get("created_on")),
            },
        )
    return transformed


def load_api_integrations(
    neo4j_session: neo4j.Session,
    integrations: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        SnowflakeApiIntegrationSchema(),
        integrations,
        lastupdated=update_tag,
        ACCOUNT_ID=account_id,
    )


def cleanup(neo4j_session: neo4j.Session, common_job_parameters: dict) -> None:
    GraphJob.from_node_schema(
        SnowflakeApiIntegrationSchema(), common_job_parameters
    ).run(neo4j_session)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: SnowflakeClient,
    common_job_parameters: dict,
) -> bool:
    """Sync Snowflake API integrations."""
    integrations = transform(get(client), client.account_id)
    logger.info(
        "Loading %d Snowflake API integrations for account %s.",
        len(integrations),
        client.account_id,
    )
    load_api_integrations(
        neo4j_session,
        integrations,
        client.account_id,
        common_job_parameters["UPDATE_TAG"],
    )
    return True
