import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.socketdev.dependency import SocketDevDependencySchema
from cartography.util import timeit

logger = logging.getLogger(__name__)
_TIMEOUT = (60, 60)
_BASE_URL = "https://api.socket.dev/v0"
_PAGE_SIZE = 100


@timeit
def get(api_token: str) -> list[dict[str, Any]]:
    """
    Fetch all dependencies for the organization using the search endpoint.
    Handles pagination via offset.
    """
    all_deps: list[dict[str, Any]] = []
    offset = 0

    while True:
        response = requests.post(
            f"{_BASE_URL}/dependencies/search",
            headers={
                "Authorization": f"Bearer {api_token}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            json={
                "limit": _PAGE_SIZE,
                "offset": offset,
            },
            timeout=_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()

        rows = data.get("rows", [])
        all_deps.extend(rows)

        if data.get("end", True) or not rows:
            break
        offset += len(rows)

    logger.debug("Fetched %d Socket.dev dependencies", len(all_deps))
    return all_deps


def transform(raw_deps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Transform raw dependency data for ingestion.
    Creates a unique ID from name + version + repository.
    """
    deps = []
    for dep in raw_deps:
        # DEBUG: print raw dependency structure to understand API format
        if not deps:
            import json

            print("=== RAW DEPENDENCY SAMPLE ===")
            print(json.dumps(dep, indent=2, default=str))
            print("==============================")

        name = dep["name"]
        version = dep["version"]
        repository = dep["repository"]
        dep_id = dep.get("id") or f"{name}|{version}|{repository}"

        deps.append(
            {
                "id": dep_id,
                "name": name,
                "version": version,
                "type": dep.get("type"),
                "namespace": dep.get("namespace"),
                "repository": repository,
                "direct": dep.get("direct"),
            },
        )
    return deps


@timeit
def load_dependencies(
    neo4j_session: neo4j.Session,
    dependencies: list[dict[str, Any]],
    org_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        SocketDevDependencySchema(),
        dependencies,
        lastupdated=update_tag,
        ORG_ID=org_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(
        SocketDevDependencySchema(),
        common_job_parameters,
    ).run(neo4j_session)


@timeit
def sync_dependencies(
    neo4j_session: neo4j.Session,
    api_token: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    Sync Socket.dev dependencies.

    The dependencies search endpoint is not org-scoped — it returns all
    dependencies visible to the API token. The caller is responsible for
    providing the correct ORG_ID in common_job_parameters.

    Returns the transformed dependencies list for downstream use (e.g. fixes sync).
    """
    logger.info("Starting Socket.dev dependencies sync")
    raw_deps = get(api_token)
    dependencies = transform(raw_deps)
    org_id = common_job_parameters["ORG_ID"]
    load_dependencies(neo4j_session, dependencies, org_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)
    logger.info("Completed Socket.dev dependencies sync")
    return dependencies
