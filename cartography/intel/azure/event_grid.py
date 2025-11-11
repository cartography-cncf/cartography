import logging
from typing import Any

import neo4j
from azure.mgmt.eventgrid import EventGridManagementClient

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.azure.event_grid_topic import AzureEventGridTopicSchema
from cartography.util import timeit

from .util.credentials import Credentials

logger = logging.getLogger(__name__)


@timeit
def get_event_grid_topics(credentials: Credentials, subscription_id: str) -> list[dict]:
    """
    Get a list of Event Grid Topics from the given Azure subscription.
    """
    client = EventGridManagementClient(credentials.credential, subscription_id)
    return [topic.as_dict() for topic in client.topics.list_by_subscription()]


def transform_event_grid_topics(topics_response: list[dict]) -> list[dict]:
    """
    Transform the raw API response to the dictionary structure that the model expects.
    """
    transformed_topics: list[dict[str, Any]] = []
    for topic in topics_response:
        transformed_topic = {
            "id": topic.get("id"),
            "name": topic.get("name"),
            "location": topic.get("location"),
            "provisioning_state": topic.get("properties", {}).get("provisioning_state"),
            "public_network_access": topic.get("properties", {}).get(
                "public_network_access"
            ),
        }
        transformed_topics.append(transformed_topic)
    return transformed_topics


@timeit
def load_event_grid_topics(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    subscription_id: str,
    update_tag: int,
) -> None:
    """
    Load the transformed Azure Event Grid Topic data to Neo4j.
    """
    load(
        neo4j_session,
        AzureEventGridTopicSchema(),
        data,
        lastupdated=update_tag,
        AZURE_SUBSCRIPTION_ID=subscription_id,
    )
    # TODO: Add logic to fetch, transform, and load Event Grid Subscriptions for each Topic.


@timeit
def cleanup_event_grid_topics(
    neo4j_session: neo4j.Session, common_job_parameters: dict
) -> None:
    """
    Run the cleanup job for Azure Event Grid Topics.
    """
    GraphJob.from_node_schema(AzureEventGridTopicSchema(), common_job_parameters).run(
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
    The main sync function for Azure Event Grid Topics.
    """
    logger.info(f"Syncing Azure Event Grid Topics for subscription {subscription_id}.")
    raw_topics = get_event_grid_topics(credentials, subscription_id)
    transformed_topics = transform_event_grid_topics(raw_topics)
    load_event_grid_topics(
        neo4j_session, transformed_topics, subscription_id, update_tag
    )
    cleanup_event_grid_topics(neo4j_session, common_job_parameters)
