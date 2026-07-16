import logging
from typing import Any

import neo4j
from msgraph import GraphServiceClient
from msgraph.generated.models.assigned_license import AssignedLicense

from cartography.client.core.tx import load_matchlinks
from cartography.graph.job import GraphJob
from cartography.intel.microsoft.entra.utils import call_with_retries
from cartography.models.microsoft.o365.user_license import EntraUserToM365LicenseRel
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
async def get_users_with_assigned_licenses(
    client: GraphServiceClient,
) -> tuple[dict[str, list[AssignedLicense]], bool]:
    """
    Fetch all users with their assignedLicenses from Microsoft Graph API.

    Uses ``GET /users?$select=id,assignedLicenses`` which is supported with
    ``User.Read.All`` application permission (unlike ``/users/{id}/licenseDetails``
    which requires delegated auth).

    Returns a tuple of (user_license_map, has_failures).

    https://learn.microsoft.com/en-us/graph/api/user-list
    """
    user_license_map: dict[str, list[AssignedLicense]] = {}
    has_failures = False

    request_configuration = client.users.UsersRequestBuilderGetRequestConfiguration(
        query_parameters=client.users.UsersRequestBuilderGetQueryParameters(
            top=999,
            select=["id", "assignedLicenses"],
        ),
    )

    try:
        page = await call_with_retries(
            lambda: client.users.get(request_configuration=request_configuration),
        )
    except Exception:
        logger.exception("Failed to fetch users with assigned licenses")
        raise

    while page:
        if page.value:
            for user in page.value:
                if user.assigned_licenses:
                    user_license_map[user.id] = user.assigned_licenses
        if not page.odata_next_link:
            break

        try:
            page = await call_with_retries(
                lambda: client.users.with_url(page.odata_next_link).get(),
            )
        except Exception as e:
            logger.error(
                "Failed to fetch next page of user licenses – "
                "stopping pagination early: %s",
                e,
            )
            has_failures = True
            break

    return user_license_map, has_failures


def transform_user_license_assignments(
    user_license_map: dict[str, list[AssignedLicense]],
) -> list[dict[str, Any]]:
    """
    Transform per-user assigned licenses into flat assignment records
    for MatchLink loading.

    Returns a list of dicts: [{"user_id": ..., "sku_id": ...}, ...]
    """
    assignments: list[dict[str, Any]] = []

    for user_id, assigned_licenses in user_license_map.items():
        for al in assigned_licenses:
            sku_id = str(al.sku_id) if al.sku_id else None
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
        _sub_resource_label="AzureTenant",
        _sub_resource_id=tenant_id,
    )


def cleanup_user_license_assignments(
    neo4j_session: neo4j.Session,
    tenant_id: str,
    update_tag: int,
) -> None:
    GraphJob.from_matchlink(
        EntraUserToM365LicenseRel(),
        "AzureTenant",
        tenant_id,
        update_tag,
    ).run(neo4j_session)


@timeit
async def sync_user_license_details(
    neo4j_session: neo4j.Session,
    client: GraphServiceClient,
    tenant_id: str,
    update_tag: int,
) -> bool:
    """
    Sync per-user license assignments by querying the users endpoint with
    ``$select=id,assignedLicenses``.

    This uses the ``User.Read.All`` application permission which is already
    granted by the Entra sync. Unlike ``/users/{id}/licenseDetails``, this
    endpoint is supported with application (client credentials) auth.

    Returns True if any failures occurred (indicating cleanup should be skipped).
    """
    logger.info(
        "Fetching user assigned licenses for tenant %s",
        tenant_id,
    )

    user_license_map, has_failures = await get_users_with_assigned_licenses(client)
    logger.info(
        "Found assigned licenses for %d users",
        len(user_license_map),
    )

    if not user_license_map:
        logger.info("No user license assignments found; skipping load")
        return has_failures

    assignments = transform_user_license_assignments(user_license_map)
    logger.info(
        "Found %d user-license assignments across %d users",
        len(assignments),
        len(user_license_map),
    )

    load_user_license_assignments(
        neo4j_session,
        assignments,
        tenant_id,
        update_tag,
    )

    return has_failures
