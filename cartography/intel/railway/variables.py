import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.railway.utils import unwrap_edges
from cartography.models.railway.variable import RailwayVariableSchema
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
    Load environment variable names from the already-fetched project bundles.

    Only names and the isSealed flag are ingested; see RailwayVariableSchema.
    """
    by_project = transform(bundles)
    load_variables(neo4j_session, by_project, update_tag)
    cleanup(neo4j_session, list(bundles), common_job_parameters)


def transform(
    bundles: dict[str, dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    by_project: dict[str, list[dict[str, Any]]] = {}
    for project_id, bundle in bundles.items():
        variables: list[dict[str, Any]] = []
        for environment in unwrap_edges(bundle["environments"]):
            variables.extend(unwrap_edges(environment["variables"]))
        by_project[project_id] = variables
    return by_project


@timeit
def load_variables(
    neo4j_session: neo4j.Session,
    by_project: dict[str, list[dict[str, Any]]],
    update_tag: int,
) -> None:
    for project_id, variables in by_project.items():
        load(
            neo4j_session,
            RailwayVariableSchema(),
            variables,
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
        scoped_job_parameters = common_job_parameters.copy()
        scoped_job_parameters["PROJECT_ID"] = project_id
        GraphJob.from_node_schema(
            RailwayVariableSchema(),
            scoped_job_parameters,
        ).run(neo4j_session)
