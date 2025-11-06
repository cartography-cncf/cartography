import logging

import neo4j
from googleapiclient.discovery import Resource

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.gcp.bigtable.backup import GCPBigtableBackupSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_bigtable_backups(client: Resource, cluster_id: str) -> list[dict]:
    backups: list[dict] = []
    request = client.projects().instances().clusters().backups().list(parent=cluster_id)
    while request is not None:
        response = request.execute()
        backups.extend(response.get("backups", []))
        request = (
            client.projects()
            .instances()
            .clusters()
            .backups()
            .list_next(
                previous_request=request,
                previous_response=response,
            )
        )
    return backups


def transform_backups(backups_data: list[dict], cluster_id: str) -> list[dict]:
    transformed: list[dict] = []
    for backup in backups_data:
        backup["cluster_id"] = cluster_id
        backup["source_table"] = backup.get("sourceTable")
        transformed.append(backup)
    return transformed


@timeit
def load_bigtable_backups(
    neo4j_session: neo4j.Session,
    data: list[dict],
    project_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        GCPBigtableBackupSchema(),
        data,
        lastupdated=update_tag,
        PROJECT_ID=project_id,
    )


@timeit
def cleanup_bigtable_backups(
    neo4j_session: neo4j.Session, common_job_parameters: dict
) -> None:
    GraphJob.from_node_schema(GCPBigtableBackupSchema(), common_job_parameters).run(
        neo4j_session,
    )


@timeit
def sync_bigtable_backups(
    neo4j_session: neo4j.Session,
    client: Resource,
    clusters: list[dict],
    project_id: str,
    update_tag: int,
    common_job_parameters: dict,
) -> None:
    logger.info(f"Syncing Bigtable Backups for project {project_id}.")
    all_backups_transformed: list[dict] = []

    for cluster in clusters:
        cluster_id = cluster["name"]
        backups_raw = get_bigtable_backups(client, cluster_id)
        all_backups_transformed.extend(transform_backups(backups_raw, cluster_id))

    load_bigtable_backups(
        neo4j_session, all_backups_transformed, project_id, update_tag
    )

    cleanup_job_params = common_job_parameters.copy()
    cleanup_job_params["PROJECT_ID"] = project_id
    cleanup_bigtable_backups(neo4j_session, cleanup_job_params)
