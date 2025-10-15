import logging
from typing import Any
from typing import Dict
from typing import List

import neo4j
from azure.core.exceptions import ClientAuthenticationError
from azure.core.exceptions import HttpResponseError
from azure.mgmt.web import WebSiteManagementClient

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.azure.function_app import AzureFunctionAppSchema
from cartography.util import timeit

from .util.credentials import Credentials

logger = logging.getLogger(__name__)


@timeit
def get_function_apps(credentials: Credentials, subscription_id: str) -> List[Dict]:
    """
    Get a list of Function Apps from the given Azure subscription.
    """
    try:
        client = WebSiteManagementClient(credentials.credential, subscription_id)
        # Note: Function Apps are a type of Web App, so we list all web apps
        # and then filter them in the transform stage.
        return [app.as_dict() for app in client.web_apps.list()]

    except ClientAuthenticationError as e:
        logger.warning(
            (
                "Failed to authenticate to get function apps for subscription '%s'. "
                "Please check your credentials. Error: %s"
            ),
            subscription_id,
            e,
        )
        return []

    except HttpResponseError as e:
        logger.warning(
            (
                "Failed to get function apps for subscription '%s' due to an API error. "
                "Status code: %s. Message: %s"
            ),
            subscription_id,
            e.status_code,
            str(e),
        )
        return []


@timeit
def transform_function_apps(function_apps_response: List[Dict]) -> List[Dict]:
    """
    Transform the raw API response to the dictionary structure that the model expects.
    """
    transformed_apps: List[Dict[str, Any]] = []
    for app in function_apps_response:
        # We only want to ingest resources that are explicitly function apps.
        if "functionapp" in app.get("kind", ""):
            transformed_app = {
                "id": app.get("id"),
                "name": app.get("name"),
                "kind": app.get("kind"),
                "location": app.get("location"),
                "state": app.get("state"),
                "default_host_name": app.get("default_host_name"),
                "https_only": app.get("https_only"),
            }
            transformed_apps.append(transformed_app)
    return transformed_apps


@timeit
def load_function_apps(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    subscription_id: str,
    update_tag: int,
) -> None:
    """
    Load the transformed Azure Function App data to Neo4j.
    """
    load(
        neo4j_session,
        AzureFunctionAppSchema(),
        data,
        lastupdated=update_tag,
        AZURE_SUBSCRIPTION_ID=subscription_id,
    )


@timeit
def cleanup_function_apps(
    neo4j_session: neo4j.Session, common_job_parameters: Dict
) -> None:
    """
    Run the cleanup job for Azure Function Apps.
    """
    GraphJob.from_node_schema(AzureFunctionAppSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    credentials: Credentials,
    subscription_id: str,
    update_tag: int,
    common_job_parameters: Dict,
) -> None:
    """
    The main sync function for Azure Function Apps.
    """
    logger.info(f"Syncing Azure Function Apps for subscription {subscription_id}.")
    raw_apps = get_function_apps(credentials, subscription_id)
    transformed_apps = transform_function_apps(raw_apps)
    load_function_apps(neo4j_session, transformed_apps, subscription_id, update_tag)
    cleanup_function_apps(neo4j_session, common_job_parameters)
