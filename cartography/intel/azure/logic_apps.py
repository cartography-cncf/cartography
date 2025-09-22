import logging
from typing import Any

import neo4j
from azure.core.exceptions import ClientAuthenticationError
from azure.core.exceptions import HttpResponseError
from azure.mgmt.logic import LogicManagementClient

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.azure.logic_apps import AzureLogicAppSchema
from cartography.util import timeit

from .util.credentials import Credentials

logger = logging.getLogger(__name__)


@timeit
def get_logic_apps(credentials: Credentials, subscription_id: str) -> list[dict]:
    """
    Get a list of Logic Apps from the given Azure subscription.
    """
    try:
        client = LogicManagementClient(credentials.credential, subscription_id)
        # NOTE: The resource for a Logic App is called a "Workflow" in the SDK.
        return [w.as_dict() for w in client.workflows.list_by_subscription()]
    except (ClientAuthenticationError, HttpResponseError) as e:
        logger.warning(
            f"Failed to get logic apps for subscription {subscription_id}: {str(e)}"
        )
        return []


def transform_logic_apps(logic_apps_response: list[dict]) -> list[dict]:
    """
    Transform the raw API response to the dictionary structure that the model expects.
    """
    transformed_apps: list[dict[str, Any]] = []
    for app in logic_apps_response:
        transformed_app = {
            "id": app.get("id"),
            "name": app.get("name"),
            "location": app.get("location"),
            "state": app.get("properties", {}).get("state"),
            "created_time": app.get("properties", {}).get("created_time"),
            "changed_time": app.get("properties", {}).get("changed_time"),
            "version": app.get("properties", {}).get("version"),
            "access_endpoint": app.get("properties", {}).get("access_endpoint"),
        }
        transformed_apps.append(transformed_app)
    return transformed_apps


@timeit
def load_logic_apps(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    subscription_id: str,
    update_tag: int,
) -> None:
    """
    Load the transformed Azure Logic App data to Neo4j.
    """
    load(
        neo4j_session,
        AzureLogicAppSchema(),
        data,
        lastupdated=update_tag,
        AZURE_SUBSCRIPTION_ID=subscription_id,
    )


@timeit
def cleanup_logic_apps(
    neo4j_session: neo4j.Session, common_job_parameters: dict
) -> None:
    """
    Run the cleanup job for Azure Logic Apps.
    """
    GraphJob.from_node_schema(AzureLogicAppSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    credentials: Credentials,
    subscription_id: str,
    update_tag: int,
    common_job_parameters: dict,
) -> None:
    """
    The main sync function for Azure Logic Apps.
    """
    logger.info(f"Syncing Azure Logic Apps for subscription {subscription_id}.")
    raw_apps = get_logic_apps(credentials, subscription_id)
    transformed_apps = transform_logic_apps(raw_apps)
    load_logic_apps(neo4j_session, transformed_apps, subscription_id, update_tag)
    cleanup_logic_apps(neo4j_session, common_job_parameters)
