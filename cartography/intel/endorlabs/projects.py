import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.endorlabs.project import EndorLabsProjectSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)
_TIMEOUT = (60, 60)
_BASE_URL = "https://api.endorlabs.com"
_PAGE_SIZE = 100


@timeit
def get(bearer_token: str, namespace: str) -> list[dict[str, Any]]:
    all_projects: list[dict[str, Any]] = []
    page_token: str | None = None
    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/jsoncompact",
    }

    while True:
        params: dict[str, Any] = {
            "list_parameters.page_size": _PAGE_SIZE,
        }
        if page_token:
            params["list_parameters.page_token"] = page_token

        response = requests.get(
            f"{_BASE_URL}/v1/namespaces/{namespace}/projects",
            headers=headers,
            params=params,
            timeout=_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()

        objects = data.get("list", {}).get("objects", [])
        all_projects.extend(objects)

        next_token = data.get("list", {}).get("response", {}).get("next_page_token")
        if not next_token or not objects:
            break
        page_token = next_token

    logger.debug("Fetched %d Endor Labs projects", len(all_projects))
    return all_projects


def transform(raw_projects: list[dict[str, Any]]) -> list[dict[str, Any]]:
    projects = []
    for project in raw_projects:
        meta = project.get("meta", {})
        spec = project.get("spec", {})
        git = spec.get("git", {})
        processing = project.get("processing_status", {})

        projects.append(
            {
                "uuid": project.get("uuid"),
                "name": meta.get("name"),
                "namespace": project.get("tenant_meta", {}).get("namespace"),
                "description": meta.get("description"),
                "platform_source": spec.get("platform_source"),
                "git_http_clone_url": git.get("http_clone_url"),
                "scan_state": processing.get("scan_state"),
            },
        )
    return projects


@timeit
def load_projects(
    neo4j_session: neo4j.Session,
    projects: list[dict[str, Any]],
    namespace_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        EndorLabsProjectSchema(),
        projects,
        lastupdated=update_tag,
        NAMESPACE_ID=namespace_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(
        EndorLabsProjectSchema(),
        common_job_parameters,
    ).run(neo4j_session)


@timeit
def sync_projects(
    neo4j_session: neo4j.Session,
    bearer_token: str,
    namespace: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> list[dict[str, Any]]:
    logger.info("Starting Endor Labs projects sync")
    raw_projects = get(bearer_token, namespace)
    projects = transform(raw_projects)

    if not projects:
        logger.warning("No Endor Labs projects found.")
        return []

    load_projects(neo4j_session, projects, namespace, update_tag)
    cleanup(neo4j_session, common_job_parameters)
    logger.info(
        "Completed Endor Labs projects sync (%d projects)",
        len(projects),
    )
    return projects
