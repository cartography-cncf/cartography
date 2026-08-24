import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.railway.utils import unwrap_edges
from cartography.models.railway.environment import RailwayEnvironmentSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
    bundles: dict[str, dict[str, Any]],
    update_tag: int,
) -> None:
    """
    Load environments from the already-fetched per-project bundles.

    :param bundles: project id -> the project bundle returned by projects.get_project_bundle
    """
    by_project = transform(bundles)
    load_environments(neo4j_session, by_project, update_tag)
    cleanup(neo4j_session, list(bundles), common_job_parameters)


def transform(
    bundles: dict[str, dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    return {
        project_id: unwrap_edges(bundle["environments"])
        for project_id, bundle in bundles.items()
    }


@timeit
def load_environments(
    neo4j_session: neo4j.Session,
    by_project: dict[str, list[dict[str, Any]]],
    update_tag: int,
) -> None:
    for project_id, environments in by_project.items():
        load(
            neo4j_session,
            RailwayEnvironmentSchema(),
            environments,
            lastupdated=update_tag,
            PROJECT_ID=project_id,
        )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    project_ids: list[str],
    common_job_parameters: dict[str, Any],
) -> None:
    for project_id in project_ids:
        # .copy() matters: mutating the shared dict would leak this project's scope into
        # every later cleanup job.
        scoped_job_parameters = common_job_parameters.copy()
        scoped_job_parameters["PROJECT_ID"] = project_id
        GraphJob.from_node_schema(
            RailwayEnvironmentSchema(),
            scoped_job_parameters,
        ).run(neo4j_session)
