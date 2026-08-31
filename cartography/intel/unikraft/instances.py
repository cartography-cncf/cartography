import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.unikraft.util import check_count_matches
from cartography.intel.unikraft.util import list_resources
from cartography.intel.unikraft.util import METRO_BASE_URLS
from cartography.intel.unikraft.util import require_non_empty
from cartography.models.unikraft.instance import UnikraftInstanceSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get(session: requests.Session, base_url: str) -> list[dict[str, Any]]:
    return list_resources(session, f"{base_url}/v1/instances", "instances")


def transform(instances: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "uuid": require_non_empty(instance.get("uuid"), "instance uuid"),
            "name": instance.get("name"),
            "created_at": instance.get("created_at"),
            "state": instance.get("state"),
            "private_fqdn": instance.get("private_fqdn"),
            "image": instance.get("image"),
            "memory_mb": instance.get("memory_mb"),
            "vcpus": instance.get("vcpus"),
            "args": instance.get("args"),
            "restart_policy": instance.get("restart_policy"),
            "start_count": instance.get("start_count"),
            "restart_count": instance.get("restart_count"),
            "started_at": instance.get("started_at"),
            "stopped_at": instance.get("stopped_at"),
            "uptime_ms": instance.get("uptime_ms"),
            "tags": instance.get("tags"),
            "status": instance.get("status"),
            "message": instance.get("message"),
            "private_ip": instance.get("private_ip"),
            "gateway": instance.get("gateway"),
            "nameserver": instance.get("nameserver"),
        }
        for instance in instances
    ]


@timeit
def load_instances(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    account_id: str,
    metro: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        UnikraftInstanceSchema(),
        data,
        lastupdated=update_tag,
        ACCOUNT_ID=account_id,
        METRO=metro,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(UnikraftInstanceSchema(), common_job_parameters).run(
        neo4j_session,
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    session: requests.Session,
    account_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
    expected_count: int | None,
) -> None:
    total_fetched = 0
    for metro, base_url in METRO_BASE_URLS.items():
        instances = get(session, base_url)
        total_fetched += len(instances)
        transformed = transform(instances)
        load_instances(neo4j_session, transformed, account_id, metro, update_tag)
    check_count_matches("instances", expected_count, total_fetched)
    cleanup(neo4j_session, common_job_parameters)
