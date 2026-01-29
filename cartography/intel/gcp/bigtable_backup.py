import logging

import neo4j
from googleapiclient.discovery import Resource
from googleapiclient.errors import HttpError

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.gcp.util import gcp_api_execute_with_retry
from cartography.intel.gcp.util import is_api_disabled_error
from cartography.models.gcp.bigtable.backup import GCPBigtableBackupSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_bigtable_backups(client: Resource, cluster_id: str) -> list[dict] | None:
    """
    Gets Bigtable backups for a cluster.

    Returns:
        list[dict]: List of Bigtable backups (empty list if cluster has no backups)
        None: If the Bigtable Admin API is not enabled or access is denied

    Raises:
        HttpError: For errors other than API disabled or permission denied
    """
    try:
        backups: list[dict] = []
        request = (
            client.projects().instances().clusters().backups().list(parent=cluster_id)
        )
        while request is not None:
            response = gcp_api_execute_with_retry(request)
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
    except HttpError as e:
        if is_api_disabled_error(e):
            logger.warning(
                "Could not retrieve Bigtable backups for cluster %s due to permissions "
                "issues or API not enabled. Skipping.",
                cluster_id,
            )
            return None
        raise


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
        # Skip this cluster if API is not enabled or access denied
        if backups_raw is not None:
            all_backups_transformed.extend(transform_backups(backups_raw, cluster_id))

    load_bigtable_backups(
        neo4j_session, all_backups_transformed, project_id, update_tag
    )

    cleanup_job_params = common_job_parameters.copy()
    cleanup_job_params["PROJECT_ID"] = project_id
    cleanup_bigtable_backups(neo4j_session, cleanup_job_params)
