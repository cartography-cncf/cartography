import logging
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

import neo4j
from azure.core.exceptions import HttpResponseError
from azure.mgmt.managementgroups import ManagementGroupsMgmtClient
from azure.mgmt.resource.subscriptions import SubscriptionClient

from cartography.client.core.tx import load
from cartography.client.core.tx import read_list_of_dicts_tx
from cartography.graph.job import GraphJob
from cartography.models.azure.subscription import AzureSubscriptionSchema
from cartography.util import timeit

from .util.credentials import Credentials

logger = logging.getLogger(__name__)


def _get_value(data: Dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in data:
            return data[key]
    return None


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


def get_azure_management_group_subscriptions(
    credentials: Credentials,
) -> tuple[List[Dict], set[str]]:
    client = ManagementGroupsMgmtClient(credentials.credential)
    management_groups = list(client.management_groups.list())
    results: List[Dict] = []
    seen_group_names: set[str] = set()
    failed_management_group_ids: set[str] = set()

    for management_group in management_groups:
        group_name = management_group.name
        if not group_name or group_name in seen_group_names:
            continue
        seen_group_names.add(group_name)

        try:
            subscriptions = list(
                client.management_group_subscriptions.get_subscriptions_under_management_group(
                    group_id=group_name,
                )
            )
        except HttpResponseError as e:
            logger.warning(
                "Failed to fetch Azure management-group subscriptions for '%s'. "
                "Skipping this management group. Details: %s",
                group_name,
                e,
            )
            failed_management_group_ids.add(
                f"/providers/Microsoft.Management/managementGroups/{group_name}",
            )
            continue

        results.extend(subscription.as_dict() for subscription in subscriptions)

    return results, failed_management_group_ids


def get_existing_subscription_parent_mappings(
    neo4j_session: neo4j.Session,
    tenant_id: str,
) -> Dict[str, str]:
    query = """
    MATCH (:AzureTenant{id: $TENANT_ID})-[:RESOURCE]->(s:AzureSubscription)-[:PARENT]->(mg:AzureManagementGroup)
    RETURN s.id AS subscriptionId, mg.id AS parent_management_group_id
    """
    rows = neo4j_session.execute_read(
        read_list_of_dicts_tx,
        query,
        TENANT_ID=tenant_id,
    )
    return {
        row["subscriptionId"]: row["parent_management_group_id"]
        for row in rows
        if row.get("subscriptionId") and row.get("parent_management_group_id")
    }


def transform_azure_subscriptions(
    subscriptions: List[Dict],
    management_group_subscriptions: List[Dict],
    existing_parent_management_group_id_by_subscription_id: Optional[
        Dict[str, str]
    ] = None,
    failed_management_group_ids: Optional[set[str]] = None,
) -> List[Dict]:
    parent_management_group_id_by_subscription_id = {}

    # Build a lookup from subscription ID to parent management group ID.
    for management_group_subscription in management_group_subscriptions:
        subscription_id = _get_value(management_group_subscription, "name")
        properties = management_group_subscription.get("properties") or {}
        parent = (
            management_group_subscription.get("parent")
            or properties.get("parent")
            or {}
        )
        parent_management_group_id = _get_value(parent, "id")

        if not subscription_id or not parent_management_group_id:
            continue

        parent_management_group_id_by_subscription_id[subscription_id] = (
            parent_management_group_id
        )

    transformed = []
    # Enrich the canonical subscription rows with management-group parent data when available.
    for subscription in subscriptions:
        transformed_subscription = dict(subscription)
        parent_management_group_id = parent_management_group_id_by_subscription_id.get(
            _get_value(subscription, "subscriptionId"),
        )
        if (
            not parent_management_group_id
            and existing_parent_management_group_id_by_subscription_id
        ):
            existing_parent_management_group_id = (
                existing_parent_management_group_id_by_subscription_id.get(
                    _get_value(subscription, "subscriptionId"),
                )
            )
            if (
                existing_parent_management_group_id
                and failed_management_group_ids
                and existing_parent_management_group_id in failed_management_group_ids
            ):
                parent_management_group_id = existing_parent_management_group_id
        if parent_management_group_id:
            transformed_subscription["parent_management_group_id"] = (
                parent_management_group_id
            )
        transformed.append(transformed_subscription)

    return transformed


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


def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict,
    cascade_delete: bool = False,
) -> None:
    GraphJob.from_node_schema(
        AzureSubscriptionSchema(),
        common_job_parameters,
        cascade_delete=cascade_delete,
    ).run(neo4j_session)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    credentials: Credentials,
    tenant_id: str,
    subscriptions: List[Dict],
    update_tag: int,
    common_job_parameters: Dict,
) -> None:
    transformed_subscriptions = subscriptions
    management_group_enrichment_failed = False

    try:
        management_group_subscriptions, failed_management_group_ids = (
            get_azure_management_group_subscriptions(
                credentials,
            )
        )
        existing_parent_management_group_id_by_subscription_id = None
        if failed_management_group_ids:
            existing_parent_management_group_id_by_subscription_id = (
                get_existing_subscription_parent_mappings(
                    neo4j_session,
                    tenant_id,
                )
            )
        transformed_subscriptions = transform_azure_subscriptions(
            subscriptions,
            management_group_subscriptions,
            existing_parent_management_group_id_by_subscription_id,
            failed_management_group_ids,
        )
    except HttpResponseError as e:
        management_group_enrichment_failed = True
        logger.warning(
            "Skipping Azure management-group subscription enrichment. "
            "Base subscription ingestion will continue. Details: %s",
            e,
        )

    # Preserve existing subscription parent edges when management-group
    # enrichment fails so the normal cleanup path does not delete them.
    if management_group_enrichment_failed:
        existing_parent_management_group_id_by_subscription_id = (
            get_existing_subscription_parent_mappings(
                neo4j_session,
                tenant_id,
            )
        )
        transformed_subscriptions = transform_azure_subscriptions(
            subscriptions,
            [],
            existing_parent_management_group_id_by_subscription_id,
            set(existing_parent_management_group_id_by_subscription_id.values()),
        )

    load_azure_subscriptions(
        neo4j_session,
        tenant_id,
        transformed_subscriptions,
        update_tag,
    )
    cleanup(neo4j_session, common_job_parameters, cascade_delete=True)
