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
from cartography.models.azure.app_service import AzureAppServiceSchema
from cartography.util import timeit

from .util.credentials import Credentials

logger = logging.getLogger(__name__)


@timeit
def get_app_services(credentials: Credentials, subscription_id: str) -> List[Dict]:
    """
    Get a list of App Services from the given Azure subscription.
    """
    try:
        client = WebSiteManagementClient(credentials.credential, subscription_id)
        # NOTE: This is the same API call as Functions. We get all web apps
        # and then filter them in the transform stage.
        return [app.as_dict() for app in client.web_apps.list()]
    except (ClientAuthenticationError, HttpResponseError) as e:
        logger.warning(
            f"Failed to get app services for subscription {subscription_id}: {str(e)}"
        )
        return []


@timeit
def transform_app_services(app_services_response: List[Dict]) -> List[Dict]:
    """
    Transform the raw API response to the dictionary structure that the model expects.
    """
    transformed_apps: List[Dict[str, Any]] = []
    for app in app_services_response:
        if "functionapp" not in app.get("kind", ""):
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
def load_app_services(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    subscription_id: str,
    update_tag: int,
) -> None:
    """
    Load the transformed Azure App Service data to Neo4j.
    """
    load(
        neo4j_session,
        AzureAppServiceSchema(),
        data,
        lastupdated=update_tag,
        AZURE_SUBSCRIPTION_ID=subscription_id,
    )


@timeit
def cleanup_app_services(
    neo4j_session: neo4j.Session, common_job_parameters: Dict
) -> None:
    """
    Run the cleanup job for Azure App Services.
    """
    GraphJob.from_node_schema(AzureAppServiceSchema(), common_job_parameters).run(
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
    The main sync function for Azure App Services.
    """
    logger.info(f"Syncing Azure App Services for subscription {subscription_id}.")
    raw_apps = get_app_services(credentials, subscription_id)
    transformed_apps = transform_app_services(raw_apps)
    load_app_services(neo4j_session, transformed_apps, subscription_id, update_tag)
    cleanup_app_services(neo4j_session, common_job_parameters)
