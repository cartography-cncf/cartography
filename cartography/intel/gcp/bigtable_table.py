import logging

import neo4j
from googleapiclient.discovery import Resource

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.gcp.bigtable.table import GCPBigtableTableSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_bigtable_tables(client: Resource, instance_id: str) -> list[dict]:
    tables: list[dict] = []
    request = client.projects().instances().tables().list(parent=instance_id)
    while request is not None:
        response = request.execute()
        tables.extend(response.get("tables", []))
        request = (
            client.projects()
            .instances()
            .tables()
            .list_next(
                previous_request=request,
                previous_response=response,
            )
        )
    return tables


def transform_tables(tables_data: list[dict], instance_id: str) -> list[dict]:
    transformed: list[dict] = []
    for table in tables_data:
        table["instance_id"] = instance_id
        transformed.append(table)
    return transformed


@timeit
def load_bigtable_tables(
    neo4j_session: neo4j.Session,
    data: list[dict],
    project_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        GCPBigtableTableSchema(),
        data,
        lastupdated=update_tag,
        PROJECT_ID=project_id,
    )


@timeit
def cleanup_bigtable_tables(
    neo4j_session: neo4j.Session, common_job_parameters: dict
) -> None:
    GraphJob.from_node_schema(GCPBigtableTableSchema(), common_job_parameters).run(
        neo4j_session,
    )


@timeit
def sync_bigtable_tables(
    neo4j_session: neo4j.Session,
    client: Resource,
    instances: list[dict],
    project_id: str,
    update_tag: int,
    common_job_parameters: dict,
) -> None:
    logger.info(f"Syncing Bigtable Tables for project {project_id}.")
    all_tables_transformed: list[dict] = []

    for inst in instances:
        instance_id = inst["name"]
        tables_raw = get_bigtable_tables(client, instance_id)
        all_tables_transformed.extend(transform_tables(tables_raw, instance_id))

    load_bigtable_tables(neo4j_session, all_tables_transformed, project_id, update_tag)

    cleanup_job_params = common_job_parameters.copy()
    cleanup_job_params["PROJECT_ID"] = project_id
    cleanup_bigtable_tables(neo4j_session, cleanup_job_params)
