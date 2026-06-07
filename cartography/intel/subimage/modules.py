from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.subimage.module import SubImageModuleSchema
from cartography.util import timeit

_TIMEOUT = (60, 60)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    tenant_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    raw_data = get(api_session, common_job_parameters["BASE_URL"])
    transformed = transform(raw_data)
    load_modules(neo4j_session, transformed, tenant_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(api_session: requests.Session, base_url: str) -> dict[str, Any]:
    response = api_session.get(f"{base_url}/api/modules/config", timeout=_TIMEOUT)
    response.raise_for_status()
    return response.json()


def transform(raw_data: dict[str, Any]) -> list[dict[str, Any]]:
    """Convert {module_name: config_dict, ...} to list of dicts with module_name key."""
    return [
        {
            "module_name": name,
            "is_configured": config.get("is_configured"),
            "last_sync_status": config.get("last_sync_status"),
        }
        for name, config in raw_data.items()
    ]


@timeit
def load_modules(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    tenant_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        SubImageModuleSchema(),
        data,
        lastupdated=update_tag,
        TENANT_ID=tenant_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(SubImageModuleSchema(), common_job_parameters).run(
        neo4j_session,
    )
