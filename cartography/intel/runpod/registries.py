from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.runpod.util import get_list
from cartography.intel.runpod.util import require_non_empty
from cartography.models.runpod.registry import RunPodRegistryCredentialSchema
from cartography.util import timeit


@timeit
def get(session: requests.Session, base_url: str) -> list[dict[str, Any]]:
    return get_list(session, base_url, "/registries", ("registries", "data"))


def transform(
    registries: list[dict[str, Any]], account_id: str
) -> list[dict[str, Any]]:
    return [
        {
            "id": require_non_empty(registry.get("id"), "registry credential id"),
            "account_id": account_id,
            "name": registry.get("name"),
        }
        for registry in registries
    ]


@timeit
def load_registries(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        RunPodRegistryCredentialSchema(),
        data,
        lastupdated=update_tag,
        RUNPOD_ACCOUNT_ID=account_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(
        RunPodRegistryCredentialSchema(), common_job_parameters
    ).run(neo4j_session)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    session: requests.Session,
    base_url: str,
    account_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    registries = get(session, base_url)
    transformed = transform(registries, account_id)
    load_registries(neo4j_session, transformed, account_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)
