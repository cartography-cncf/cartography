import logging
from typing import Any

import neo4j
from msgraph import GraphServiceClient
from msgraph.generated.models.subscribed_sku import SubscribedSku

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.microsoft.entra.utils import call_with_retries
from cartography.models.microsoft.o365.license import M365LicenseSchema
from cartography.models.microsoft.o365.service_plan import M365ServicePlanSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
async def get_subscribed_skus(
    client: GraphServiceClient,
) -> list[SubscribedSku]:
    """
    Get all subscribed SKUs (license subscriptions) from Microsoft Graph API.

    https://learn.microsoft.com/en-us/graph/api/subscribedsku-list
    """
    response = await call_with_retries(client.subscribed_skus.get)
    return response.value if response and response.value else []


def transform_licenses(
    skus: list[SubscribedSku],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """
    Transform SubscribedSku objects into license dicts and service plan dicts.

    Returns a tuple of (license_dicts, service_plan_dicts).
    Service plans are deduplicated by service_plan_id and collect all parent
    license sku_ids for one-to-many relationship creation.
    """
    licenses: list[dict[str, Any]] = []
    # Keyed by service_plan_id to deduplicate across licenses
    service_plan_map: dict[str, dict[str, Any]] = {}

    for sku in skus:
        sku_id_str = str(sku.sku_id) if sku.sku_id else None
        prepaid = sku.prepaid_units

        licenses.append(
            {
                "id": sku.id,
                "sku_id": sku_id_str,
                "sku_part_number": sku.sku_part_number,
                "capability_status": sku.capability_status,
                "applies_to": sku.applies_to,
                "consumed_units": sku.consumed_units,
                "prepaid_enabled": prepaid.enabled if prepaid else None,
                "prepaid_suspended": prepaid.suspended if prepaid else None,
                "prepaid_warning": prepaid.warning if prepaid else None,
            }
        )

        for sp in sku.service_plans or []:
            sp_id = str(sp.service_plan_id) if sp.service_plan_id else None
            if sp_id is None:
                continue

            if sp_id in service_plan_map:
                # Same service plan appears in multiple licenses; collect
                # all parent license IDs for the one-to-many relationship.
                existing_ids = service_plan_map[sp_id]["license_ids"]
                if sku.id and sku.id not in existing_ids:
                    existing_ids.append(sku.id)
            else:
                service_plan_map[sp_id] = {
                    "id": sp_id,
                    "service_plan_name": sp.service_plan_name,
                    "provisioning_status": sp.provisioning_status,
                    "applies_to": sp.applies_to,
                    "license_ids": [sku.id] if sku.id else [],
                }

    service_plans = list(service_plan_map.values())
    return licenses, service_plans


@timeit
def load_licenses(
    neo4j_session: neo4j.Session,
    licenses: list[dict[str, Any]],
    tenant_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        M365LicenseSchema(),
        licenses,
        lastupdated=update_tag,
        TENANT_ID=tenant_id,
    )


@timeit
def load_service_plans(
    neo4j_session: neo4j.Session,
    service_plans: list[dict[str, Any]],
    tenant_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        M365ServicePlanSchema(),
        service_plans,
        lastupdated=update_tag,
        TENANT_ID=tenant_id,
    )


def cleanup_licenses(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(M365LicenseSchema(), common_job_parameters).run(
        neo4j_session,
    )


def cleanup_service_plans(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(M365ServicePlanSchema(), common_job_parameters).run(
        neo4j_session,
    )


@timeit
async def sync_licenses(
    neo4j_session: neo4j.Session,
    client: GraphServiceClient,
    tenant_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Sync M365 license subscriptions and their service plans.
    """
    logger.info("Fetching M365 subscribed SKUs")
    skus = await get_subscribed_skus(client)
    logger.info("Retrieved %d subscribed SKUs", len(skus))

    licenses, service_plans = transform_licenses(skus)

    load_licenses(neo4j_session, licenses, tenant_id, update_tag)
    load_service_plans(neo4j_session, service_plans, tenant_id, update_tag)

    cleanup_licenses(neo4j_session, common_job_parameters)
    cleanup_service_plans(neo4j_session, common_job_parameters)
