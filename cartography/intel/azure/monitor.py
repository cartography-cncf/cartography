import logging
from typing import Any

import neo4j
from azure.core.exceptions import HttpResponseError
from azure.mgmt.monitor import MonitorManagementClient

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.azure.monitor import AzureMonitorMetricAlertSchema
from cartography.util import timeit

from .util.credentials import Credentials

logger = logging.getLogger(__name__)


@timeit
def get_metric_alerts(client: MonitorManagementClient) -> list[dict]:
    """
    Get a list of Metric Alerts from the given Azure subscription.
    """
    try:
        return [
            alert.as_dict() for alert in client.metric_alerts.list_by_subscription()
        ]
    except HttpResponseError:
        logger.warning(
            "Failed to get Azure Monitor Metric Alerts due to a transient error.",
            exc_info=True,
        )
        return []


def transform_metric_alerts(metric_alerts: list[dict]) -> list[dict]:
    """
    Transform the raw API response to the dictionary structure that the model expects.
    """
    transformed_alerts: list[dict[str, Any]] = []
    for alert in metric_alerts:
        transformed_alert = {
            "id": alert.get("id"),
            "name": alert.get("name"),
            "location": alert.get("location"),
            "description": alert.get("description"),
            "severity": alert.get("severity"),
            "enabled": alert.get("enabled"),
            "window_size": str(alert.get("window_size")),
            "evaluation_frequency": str(alert.get("evaluation_frequency")),
            "last_updated_time": alert.get("properties", {}).get("last_updated_time"),
        }
        transformed_alerts.append(transformed_alert)
    return transformed_alerts


@timeit
def load_metric_alerts(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    subscription_id: str,
    update_tag: int,
) -> None:
    """
    Load the transformed Azure Monitor Metric Alert data to Neo4j.
    """
    load(
        neo4j_session,
        AzureMonitorMetricAlertSchema(),
        data,
        lastupdated=update_tag,
        AZURE_SUBSCRIPTION_ID=subscription_id,
    )


@timeit
def cleanup_metric_alerts(
    neo4j_session: neo4j.Session, common_job_parameters: dict
) -> None:
    """
    Run the cleanup job for Azure Monitor Metric Alerts.
    """
    GraphJob.from_node_schema(
        AzureMonitorMetricAlertSchema(), common_job_parameters
    ).run(neo4j_session)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    credentials: Credentials,
    subscription_id: str,
    update_tag: int,
    common_job_parameters: dict,
) -> None:
    """
    The main sync function for Azure Monitor.
    """
    logger.info(
        f"Syncing Azure Monitor Metric Alerts for subscription {subscription_id}."
    )
    client = MonitorManagementClient(credentials.credential, subscription_id)
    raw_alerts = get_metric_alerts(client)
    transformed_alerts = transform_metric_alerts(raw_alerts)
    load_metric_alerts(neo4j_session, transformed_alerts, subscription_id, update_tag)
    cleanup_metric_alerts(neo4j_session, common_job_parameters)
