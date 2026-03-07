import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.models.subimage.tenant import SubImageTenantSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)
_TIMEOUT = (60, 60)


@timeit
def get(api_session: requests.Session, base_url: str) -> list[dict[str, Any]]:
    response = api_session.get(f"{base_url}/api/tenant", timeout=_TIMEOUT)
    response.raise_for_status()
    tenant_data = response.json()
    tenant_data["id"] = tenant_data.get("tenantId", "")
    return [tenant_data]


@timeit
def load_tenants(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    update_tag: int,
) -> None:
    logger.info("Loading %d SubImage Tenants into Neo4j.", len(data))
    load(
        neo4j_session,
        SubImageTenantSchema(),
        data,
        lastupdated=update_tag,
    )
