from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.subimage.neo4juser import SubImageNeo4jUserSchema
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
    load_neo4jusers(neo4j_session, transformed, tenant_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(api_session: requests.Session, base_url: str) -> dict[str, Any]:
    response = api_session.get(f"{base_url}/api/api-keys/neo4j", timeout=_TIMEOUT)
    response.raise_for_status()
    return response.json()


def transform(raw_data: dict[str, Any]) -> list[dict[str, Any]]:
    """Convert {"usernames": ["a", "b"]} to [{"username": "a"}, {"username": "b"}]."""
    return [{"username": username} for username in raw_data["usernames"]]


@timeit
def load_neo4jusers(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    tenant_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        SubImageNeo4jUserSchema(),
        data,
        lastupdated=update_tag,
        TENANT_ID=tenant_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(SubImageNeo4jUserSchema(), common_job_parameters).run(
        neo4j_session,
    )
