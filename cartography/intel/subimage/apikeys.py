from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.subimage.apikey import SubImageAPIKeySchema
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
    apikeys = transform(raw_data)
    load_apikeys(neo4j_session, apikeys, tenant_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(api_session: requests.Session, base_url: str) -> list[dict[str, Any]]:
    response = api_session.get(f"{base_url}/api/api-keys/subimage", timeout=_TIMEOUT)
    response.raise_for_status()
    return response.json()


def transform(raw_data: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "app_id": key["app_id"],
            "client_id": key.get("client_id"),
            "role": key.get("role"),
            "name": key.get("name"),
            "description": key.get("description"),
        }
        for key in raw_data
    ]


@timeit
def load_apikeys(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    tenant_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        SubImageAPIKeySchema(),
        data,
        lastupdated=update_tag,
        TENANT_ID=tenant_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(SubImageAPIKeySchema(), common_job_parameters).run(
        neo4j_session,
    )
