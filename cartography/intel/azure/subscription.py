import logging
from typing import Dict
from typing import List
from typing import Optional

import neo4j
from azure.core.exceptions import HttpResponseError
from azure.mgmt.resource import SubscriptionClient

from cartography.util import run_cleanup_job
from cartography.util import timeit

from .util.credentials import Credentials

logger = logging.getLogger(__name__)


def get_all_azure_subscriptions(credentials: Credentials) -> List[Dict]:
    try:
        # Create the client
        client = SubscriptionClient(credentials.arm_credentials)

        # Get all the accessible subscriptions
        subs = list(client.subscriptions.list())

    except HttpResponseError as e:
        logger.error(
            f"failed to fetch subscriptions for the credentials \
            The provided credentials do not have access to any subscriptions - \
            {e}",
        )

        return []

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
        client = SubscriptionClient(credentials.arm_credentials)

        # Get all the accessible subscriptions
        sub = client.subscriptions.get(subscription_id)

    except HttpResponseError as e:
        logger.error(
            f"failed to fetch subscription for the credentials \
            The provided credentials do not have access to this subscription: {subscription_id} - \
            {e}",
        )

        return []

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
    query = """
    MERGE (at:AzureTenant{id: $TENANT_ID})
    ON CREATE SET at.firstseen = timestamp()
    SET at.lastupdated = $update_tag
    WITH at
    MERGE (as:AzureSubscription{id: $SUBSCRIPTION_ID})
    ON CREATE SET as.firstseen = timestamp(), as.path = $SUBSCRIPTION_PATH
    SET as.lastupdated = $update_tag, as.name = $SUBSCRIPTION_NAME, as.state = $SUBSCRIPTION_STATE
    WITH as, at
    MERGE (at)-[r:RESOURCE]->(as)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag;
    """
    for sub in subscriptions:
        neo4j_session.run(
            query,
            TENANT_ID=tenant_id,
            SUBSCRIPTION_ID=sub["subscriptionId"],
            SUBSCRIPTION_PATH=sub["id"],
            SUBSCRIPTION_NAME=sub["displayName"],
            SUBSCRIPTION_STATE=sub["state"],
            update_tag=update_tag,
        )


def cleanup(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job(
        "azure_subscriptions_cleanup.json",
        neo4j_session,
        common_job_parameters,
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
