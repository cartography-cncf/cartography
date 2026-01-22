import logging

import neo4j
from googleapiclient.discovery import Resource

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.gcp.bigtable.instance import GCPBigtableInstanceSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_bigtable_instances(client: Resource, project_id: str) -> list[dict]:
    instances: list[dict] = []
    request = client.projects().instances().list(parent=f"projects/{project_id}")
    while request is not None:
        response = request.execute()
        instances.extend(response.get("instances", []))
        request = (
            client.projects()
            .instances()
            .list_next(
                previous_request=request,
                previous_response=response,
            )
        )
    return instances


def transform_instances(instances_data: list[dict], project_id: str) -> list[dict]:
    transformed: list[dict] = []
    for inst in instances_data:
        inst["project_id"] = project_id
        transformed.append(inst)
    return transformed


@timeit
def load_bigtable_instances(
    neo4j_session: neo4j.Session,
    data: list[dict],
    project_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        GCPBigtableInstanceSchema(),
        data,
        lastupdated=update_tag,
        PROJECT_ID=project_id,
    )


@timeit
def cleanup_bigtable_instances(
    neo4j_session: neo4j.Session, common_job_parameters: dict
) -> None:
    GraphJob.from_node_schema(GCPBigtableInstanceSchema(), common_job_parameters).run(
        neo4j_session,
    )


@timeit
def sync_bigtable_instances(
    neo4j_session: neo4j.Session,
    client: Resource,
    project_id: str,
    update_tag: int,
    common_job_parameters: dict,
) -> list[dict]:
    logger.info(f"Syncing Bigtable Instances for project {project_id}.")
    instances_raw = get_bigtable_instances(client, project_id)
    if not instances_raw:
        logger.info(f"No Bigtable instances found for project {project_id}.")
        return []

    instances = transform_instances(instances_raw, project_id)
    load_bigtable_instances(neo4j_session, instances, project_id, update_tag)

    cleanup_job_params = common_job_parameters.copy()
    cleanup_job_params["PROJECT_ID"] = project_id
    cleanup_bigtable_instances(neo4j_session, cleanup_job_params)

    return instances_raw
