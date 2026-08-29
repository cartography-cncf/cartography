import logging
from typing import Any

import neo4j
import scaleway
from scaleway.jobs.v1alpha1 import JobDefinition
from scaleway.jobs.v1alpha1 import JobsV1Alpha1API

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.scaleway.utils import list_all_regions
from cartography.intel.scaleway.utils import scaleway_obj_to_dict
from cartography.models.scaleway.serverless.job_definition import (
    ScalewayServerlessJobDefinitionSchema,
)
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: scaleway.Client,
    common_job_parameters: dict[str, Any],
    org_id: str,
    projects_id: list[str],
    update_tag: int,
) -> None:
    job_definitions = get(client, org_id)
    job_definitions_by_project = transform(job_definitions)
    load_job_definitions(neo4j_session, job_definitions_by_project, update_tag)
    cleanup(neo4j_session, projects_id, common_job_parameters)


@timeit
def get(client: scaleway.Client, org_id: str) -> list[JobDefinition]:
    api = JobsV1Alpha1API(client)
    return list_all_regions(api.list_job_definitions_all, organization_id=org_id)


def transform(
    job_definitions: list[JobDefinition],
) -> dict[str, list[dict[str, Any]]]:
    job_definitions_by_project: dict[str, list[dict[str, Any]]] = {}
    for job_definition in job_definitions:
        formatted = scaleway_obj_to_dict(job_definition)
        # Flatten the nested cron_schedule object into scalar fields.
        cron = formatted.pop("cron_schedule", None) or {}
        formatted["cron_schedule"] = cron.get("schedule")
        formatted["cron_timezone"] = cron.get("timezone")
        job_definitions_by_project.setdefault(job_definition.project_id, []).append(
            formatted
        )
    return job_definitions_by_project


@timeit
def load_job_definitions(
    neo4j_session: neo4j.Session,
    job_definitions_by_project: dict[str, list[dict[str, Any]]],
    update_tag: int,
) -> None:
    for project_id, job_definitions in job_definitions_by_project.items():
        logger.info(
            "Loading %d Scaleway job definitions in project '%s' into Neo4j.",
            len(job_definitions),
            project_id,
        )
        load(
            neo4j_session,
            ScalewayServerlessJobDefinitionSchema(),
            job_definitions,
            lastupdated=update_tag,
            PROJECT_ID=project_id,
        )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    projects_id: list[str],
    common_job_parameters: dict[str, Any],
) -> None:
    for project_id in projects_id:
        scoped_job_parameters = common_job_parameters.copy()
        scoped_job_parameters["PROJECT_ID"] = project_id
        GraphJob.from_node_schema(
            ScalewayServerlessJobDefinitionSchema(), scoped_job_parameters
        ).run(neo4j_session)
