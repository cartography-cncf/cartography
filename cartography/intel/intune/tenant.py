import logging
from typing import Any

import neo4j
from msgraph import GraphServiceClient
from msgraph.generated.models.organization import Organization

from cartography.client.core.tx import load
from cartography.models.intune.tenant import IntuneTenantSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
async def get_tenant(client: GraphServiceClient) -> dict[str, Any]:
    """
    Get tenant information from Microsoft Graph API.
    """
    org = await client.organization.get()
    tenant: Organization = org.value[0]
    return {
        "id": tenant.id,
        "display_name": tenant.display_name,
    }


@timeit
def load_tenant(
    neo4j_session: neo4j.Session,
    tenant: dict[str, Any],
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        IntuneTenantSchema(),
        [tenant],
        lastupdated=update_tag,
    )


@timeit
async def sync_tenant(
    neo4j_session: neo4j.Session,
    client: GraphServiceClient,
    update_tag: int,
) -> None:
    tenant = await get_tenant(client)
    load_tenant(neo4j_session, tenant, update_tag)
