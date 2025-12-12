import logging
from typing import Dict
from typing import List
from typing import Optional

import neo4j
from azure.core.exceptions import HttpResponseError
from azure.mgmt.resource import SubscriptionClient

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.azure.subscription import AzureSubscriptionSchema
from cartography.util import timeit

from .util.credentials import Credentials

logger = logging.getLogger(__name__)


def get_all_azure_subscriptions(credentials: Credentials) -> List[Dict]:
    try:
        # Create the client
        client = SubscriptionClient(credentials.credential)

        # Get all the accessible subscriptions
        subs = list(client.subscriptions.list())

    except HttpResponseError as e:
        raise RuntimeError(
            f"Failed to fetch subscriptions for the credentials. "
            f"The provided credentials do not have access to any subscriptions: {e}",
        ) from e

    subscriptions = []
    for sub in subs:
        subscriptions.append(
            {
                "id": sub.id,
                "subscriptionId": sub.subscription_id,
                "displayName": sub.display_name,
                "state": sub.state,
            },
        )

    return subscriptions


def get_current_azure_subscription(
    credentials: Credentials,
    subscription_id: Optional[str],
) -> List[Dict]:
    try:
        # Create the client
        client = SubscriptionClient(credentials.credential)

        # Get all the accessible subscriptions
        sub = client.subscriptions.get(subscription_id)

    except HttpResponseError as e:
        raise RuntimeError(
            f"Failed to fetch subscription for the credentials. "
            f"The provided credentials do not have access to this subscription: {subscription_id}: {e}",
        ) from e

    return [
        {
            "id": sub.id,
            "subscriptionId": sub.subscription_id,
            "displayName": sub.display_name,
            "state": sub.state,
        },
    ]


def load_azure_subscriptions(
    neo4j_session: neo4j.Session,
    tenant_id: str,
    subscriptions: List[Dict],
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        AzureSubscriptionSchema(),
        subscriptions,
        lastupdated=update_tag,
        TENANT_ID=tenant_id,
    )


def cleanup(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    GraphJob.from_node_schema(AzureSubscriptionSchema(), common_job_parameters).run(
        neo4j_session,
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    tenant_id: str,
    subscriptions: List[Dict],
    update_tag: int,
    common_job_parameters: Dict,
) -> None:
    load_azure_subscriptions(neo4j_session, tenant_id, subscriptions, update_tag)
    cleanup(neo4j_session, common_job_parameters)
