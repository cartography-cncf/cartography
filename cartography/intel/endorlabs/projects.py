import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.endorlabs.util import paginated_get
from cartography.models.endorlabs.project import EndorLabsProjectSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get(bearer_token: str, namespace: str) -> list[dict[str, Any]]:
    return paginated_get(bearer_token, namespace, "projects")


def transform(raw_projects: list[dict[str, Any]]) -> list[dict[str, Any]]:
    projects = []
    for project in raw_projects:
        meta = project.get("meta", {})
        spec = project.get("spec", {})
        git = spec.get("git", {})
        processing = project.get("processing_status", {})

        projects.append(
            {
                "uuid": project["uuid"],
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
        cleanup(neo4j_session, common_job_parameters)
        return []

    load_projects(neo4j_session, projects, namespace, update_tag)
    cleanup(neo4j_session, common_job_parameters)
    logger.info(
        "Completed Endor Labs projects sync (%d projects)",
        len(projects),
    )
    return projects
