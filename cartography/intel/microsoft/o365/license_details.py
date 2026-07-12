import asyncio
import logging
from typing import Any

import neo4j
from kiota_abstractions.api_error import APIError
from msgraph import GraphServiceClient
from msgraph.generated.models.license_details import LicenseDetails

from cartography.client.core.tx import load_matchlinks
from cartography.graph.job import GraphJob
from cartography.intel.microsoft.entra.utils import call_with_retries
from cartography.models.microsoft.o365.user_license import EntraUserToM365LicenseRel
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
async def get_user_license_details(
    client: GraphServiceClient,
    user_ids: list[str],
) -> tuple[dict[str, list[LicenseDetails]], bool]:
    """
    Fetch license details for each user from Microsoft Graph API concurrently.

    Returns a tuple of (user_license_map, has_failures).

    https://learn.microsoft.com/en-us/graph/api/user-list-licensedetails
    """
    user_license_map: dict[str, list[LicenseDetails]] = {}
    has_failures = False
    semaphore = asyncio.Semaphore(20)

    async def fetch_for_user(user_id: str) -> None:
        nonlocal has_failures
        async with semaphore:
            try:
                response = await call_with_retries(
                    lambda uid=user_id: client.users.by_user_id(
                        uid
                    ).license_details.get(),
                )
                if response and response.value:
                    user_license_map[user_id] = response.value
            except APIError as e:
                # 404 --> the user was deleted between user-sync and license-sync.
                # 403 --> insufficient permissions for this specific user.
                # Both are non-fatal: skip and continue, but mark as failure for cleanup.
                if e.response_status_code in (403, 404):
                    logger.debug(
                        "Skipping license details for user %s: %d %s",
                        user_id,
                        e.response_status_code,
                        e.message,
                    )
                    has_failures = True
                    return
                raise

    await asyncio.gather(*(fetch_for_user(uid) for uid in user_ids))
    return user_license_map, has_failures


def transform_user_license_assignments(
    user_license_map: dict[str, list[LicenseDetails]],
) -> list[dict[str, Any]]:
    """
    Transform per-user license details into flat assignment records
    for MatchLink loading.

    Returns a list of dicts: [{"user_id": ..., "sku_id": ...}, ...]
    """
    assignments: list[dict[str, Any]] = []

    for user_id, license_details in user_license_map.items():
        for ld in license_details:
            sku_id = str(ld.sku_id) if ld.sku_id else None
            if sku_id is None:
                continue
            assignments.append(
                {
                    "user_id": user_id,
                    "sku_id": sku_id,
                }
            )

    return assignments


@timeit
def load_user_license_assignments(
    neo4j_session: neo4j.Session,
    assignments: list[dict[str, Any]],
    tenant_id: str,
    update_tag: int,
) -> None:
    if not assignments:
        return
    load_matchlinks(
        neo4j_session,
        EntraUserToM365LicenseRel(),
        assignments,
        lastupdated=update_tag,
        _sub_resource_label="EntraTenant",
        _sub_resource_id=tenant_id,
    )


def cleanup_user_license_assignments(
    neo4j_session: neo4j.Session,
    tenant_id: str,
    update_tag: int,
) -> None:
    GraphJob.from_matchlink(
        EntraUserToM365LicenseRel(),
        "EntraTenant",
        tenant_id,
        update_tag,
    ).run(neo4j_session)


@timeit
async def sync_user_license_details(
    neo4j_session: neo4j.Session,
    client: GraphServiceClient,
    tenant_id: str,
    update_tag: int,
) -> None:
    """
    Sync per-user license assignments by querying existing EntraUser nodes
    and fetching their license details from the Graph API.
    """
    # Query Neo4j for all EntraUser IDs in this tenant
    result = neo4j_session.run(
        """
        MATCH (t:EntraTenant {id: $TENANT_ID})-[:RESOURCE]->(u:EntraUser)
        RETURN u.id AS user_id
        """,
        TENANT_ID=tenant_id,
    )
    user_ids = [record["user_id"] for record in result]
    logger.info(
        "Fetching license details for %d Entra users in tenant %s",
        len(user_ids),
        tenant_id,
    )

    if not user_ids:
        logger.info("No Entra users found; skipping license detail sync")
        return

    # Fetch license details in batches to control memory
    batch_size = 200
    all_assignments: list[dict[str, Any]] = []
    has_failures = False

    for i in range(0, len(user_ids), batch_size):
        batch = user_ids[i : i + batch_size]
        user_license_map, batch_has_failures = await get_user_license_details(
            client, batch
        )
        if batch_has_failures:
            has_failures = True

        assignments = transform_user_license_assignments(user_license_map)
        all_assignments.extend(assignments)

    logger.info(
        "Found %d user-license assignments across %d users",
        len(all_assignments),
        len(user_ids),
    )

    load_user_license_assignments(
        neo4j_session,
        all_assignments,
        tenant_id,
        update_tag,
    )

    if has_failures:
        logger.warning(
            "One or more user license detail fetches failed or were skipped. "
            "Bypassing ASSIGNED_LICENSE cleanup to prevent accidental data loss."
        )
    else:
        cleanup_user_license_assignments(neo4j_session, tenant_id, update_tag)
