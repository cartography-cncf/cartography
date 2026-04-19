from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.subimage.framework import SubImageFrameworkSchema
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
    frameworks = transform(raw_data)
    load_frameworks(neo4j_session, frameworks, tenant_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(api_session: requests.Session, base_url: str) -> list[dict[str, Any]]:
    response = api_session.get(
        f"{base_url}/api/findings/frameworks",
        timeout=_TIMEOUT,
    )
    response.raise_for_status()
    return response.json()["frameworks"]


def transform(raw_data: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "id": fw["id"],
            "name": fw.get("name"),
            "short_name": fw.get("short_name"),
            "scope": fw.get("scope"),
            "revision": fw.get("revision"),
            "enabled": fw.get("enabled"),
            "enabled_at": fw.get("enabled_at"),
            "disabled_at": fw.get("disabled_at"),
            "rule_count": fw.get("rule_count"),
        }
        for fw in raw_data
    ]


@timeit
def load_frameworks(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    tenant_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        SubImageFrameworkSchema(),
        data,
        lastupdated=update_tag,
        TENANT_ID=tenant_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(SubImageFrameworkSchema(), common_job_parameters).run(
        neo4j_session,
    )
