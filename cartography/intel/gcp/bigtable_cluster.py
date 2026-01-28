import logging

import neo4j
from googleapiclient.discovery import Resource
from googleapiclient.errors import HttpError

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.gcp.util import gcp_api_execute_with_retry
from cartography.intel.gcp.util import is_api_disabled_error
from cartography.models.gcp.bigtable.cluster import GCPBigtableClusterSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_bigtable_clusters(client: Resource, instance_id: str) -> list[dict] | None:
    """
    Gets Bigtable clusters for an instance.

    Returns:
        list[dict]: List of Bigtable clusters (empty list if instance has no clusters)
        None: If the Bigtable Admin API is not enabled or access is denied

    Raises:
        HttpError: For errors other than API disabled or permission denied
    """
    try:
        clusters: list[dict] = []
        request = client.projects().instances().clusters().list(parent=instance_id)
        while request is not None:
            response = gcp_api_execute_with_retry(request)
            clusters.extend(response.get("clusters", []))
            request = (
                client.projects()
                .instances()
                .clusters()
                .list_next(
                    previous_request=request,
                    previous_response=response,
                )
            )
        return clusters
    except HttpError as e:
        if is_api_disabled_error(e):
            logger.warning(
                "Could not retrieve Bigtable clusters for instance %s due to permissions "
                "issues or API not enabled. Skipping.",
                instance_id,
            )
            return None
        raise


def transform_clusters(clusters_data: list[dict], instance_id: str) -> list[dict]:
    transformed: list[dict] = []
    for cluster in clusters_data:
        cluster["instance_id"] = instance_id
        transformed.append(cluster)
    return transformed


@timeit
def load_bigtable_clusters(
    neo4j_session: neo4j.Session,
    data: list[dict],
    project_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        GCPBigtableClusterSchema(),
        data,
        lastupdated=update_tag,
        PROJECT_ID=project_id,
    )


@timeit
def cleanup_bigtable_clusters(
    neo4j_session: neo4j.Session, common_job_parameters: dict
) -> None:
    GraphJob.from_node_schema(GCPBigtableClusterSchema(), common_job_parameters).run(
        neo4j_session,
    )


@timeit
def sync_bigtable_clusters(
    neo4j_session: neo4j.Session,
    client: Resource,
    instances: list[dict],
    project_id: str,
    update_tag: int,
    common_job_parameters: dict,
) -> list[dict]:
    logger.info(f"Syncing Bigtable Clusters for project {project_id}.")
    all_clusters_raw: list[dict] = []
    all_clusters_transformed: list[dict] = []

    for inst in instances:
        instance_id = inst["name"]
        clusters_raw = get_bigtable_clusters(client, instance_id)
        # Skip this instance if API is not enabled or access denied
        if clusters_raw is not None:
            all_clusters_raw.extend(clusters_raw)
            all_clusters_transformed.extend(
                transform_clusters(clusters_raw, instance_id)
            )

    load_bigtable_clusters(
        neo4j_session, all_clusters_transformed, project_id, update_tag
    )

    cleanup_job_params = common_job_parameters.copy()
    cleanup_job_params["PROJECT_ID"] = project_id
    cleanup_bigtable_clusters(neo4j_session, cleanup_job_params)

    return all_clusters_raw
