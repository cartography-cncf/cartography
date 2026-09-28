"""Snowflake notification integrations.

The ``notification_hook`` sub-object holds the queue coordinates (the SNS topic and
its assumed role, the Azure storage queue, the Pub/Sub topic) and is flattened onto
the node so the SNS and IAM edges can be matched directly.
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
from cartography.models.snowflake.notification_integration import (
    SnowflakeNotificationIntegrationSchema,
)
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get(client: SnowflakeClient) -> list[dict[str, Any]]:
    return client.list_all("/api/v2/notification-integrations")


def transform(
    integrations: list[dict[str, Any]],
    account_id: str,
) -> list[dict[str, Any]]:
    transformed: list[dict[str, Any]] = []
    for integration in integrations:
        name = integration["name"]
        hook = integration.get("notification_hook") or {}
        transformed.append(
            {
                "id": sf_id(account_id, "notification_integration", sf_fqn(name)),
                "name": name,
                "enabled": integration.get("enabled"),
                "notification_hook_type": hook.get("type"),
                "aws_sns_topic_arn": hook.get("aws_sns_topic_arn"),
                "aws_sns_role_arn": hook.get("aws_sns_role_arn"),
                "aws_sns_external_id": hook.get("aws_sns_external_id"),
                "azure_storage_queue_primary_uri": hook.get(
                    "azure_storage_queue_primary_uri"
                ),
                "azure_tenant_id": hook.get("azure_tenant_id"),
                "gcp_pubsub_subscription_name": hook.get(
                    "gcp_pubsub_subscription_name"
                ),
                "gcp_pubsub_topic_name": hook.get("gcp_pubsub_topic_name"),
                "comment": integration.get("comment"),
                "created_on": iso_to_datetime(integration.get("created_on")),
            },
        )
    return transformed


def load_notification_integrations(
    neo4j_session: neo4j.Session,
    integrations: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        SnowflakeNotificationIntegrationSchema(),
        integrations,
        lastupdated=update_tag,
        ACCOUNT_ID=account_id,
    )


def cleanup(neo4j_session: neo4j.Session, common_job_parameters: dict) -> None:
    GraphJob.from_node_schema(
        SnowflakeNotificationIntegrationSchema(), common_job_parameters
    ).run(neo4j_session)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: SnowflakeClient,
    common_job_parameters: dict,
) -> bool:
    """Sync Snowflake notification integrations."""
    integrations = transform(get(client), client.account_id)
    logger.info(
        "Loading %d Snowflake notification integrations for account %s.",
        len(integrations),
        client.account_id,
    )
    load_notification_integrations(
        neo4j_session,
        integrations,
        client.account_id,
        common_job_parameters["UPDATE_TAG"],
    )
    return True
