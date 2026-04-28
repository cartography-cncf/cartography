from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.models.subimage.tenant import SubImageTenantSchema
from cartography.util import timeit

_TIMEOUT = (60, 60)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    update_tag: int,
    base_url: str,
) -> list[dict[str, Any]]:
    raw = get(api_session, base_url)
    tenants = transform(raw)
    load_tenants(neo4j_session, tenants, update_tag)
    return tenants


@timeit
def get(api_session: requests.Session, base_url: str) -> list[dict[str, Any]]:
    response = api_session.get(f"{base_url}/api/tenant", timeout=_TIMEOUT)
    response.raise_for_status()
    return [response.json()]


@timeit
def transform(raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result = []
    for tenant in raw:
        result.append(
            {
                "id": tenant["tenantId"],
                "account_id": tenant["accountId"],
                "scan_role_name": tenant["scanRoleName"],
            }
        )
    return result


@timeit
def load_tenants(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        SubImageTenantSchema(),
        data,
        lastupdated=update_tag,
    )
