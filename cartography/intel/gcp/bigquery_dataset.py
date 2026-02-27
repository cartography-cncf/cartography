import logging

import neo4j
from googleapiclient.discovery import Resource
from googleapiclient.errors import HttpError

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.gcp.util import gcp_api_execute_with_retry
from cartography.intel.gcp.util import is_api_disabled_error
from cartography.models.gcp.bigquery.dataset import GCPBigQueryDatasetSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_bigquery_datasets(client: Resource, project_id: str) -> list[dict] | None:
    """
    Gets BigQuery datasets for a project.

    Returns:
        list[dict]: List of BigQuery datasets (empty list if project has no datasets)
        None: If the BigQuery API is not enabled or access is denied

    Raises:
        HttpError: For errors other than API disabled or permission denied
    """
    try:
        datasets: list[dict] = []
        request = client.datasets().list(projectId=project_id, all=True)
        while request is not None:
            response = gcp_api_execute_with_retry(request)
            datasets.extend(response.get("datasets", []))
            request = client.datasets().list_next(
                previous_request=request,
                previous_response=response,
            )
        return datasets
    except HttpError as e:
        if is_api_disabled_error(e):
            logger.warning(
                "Could not retrieve BigQuery datasets on project %s due to permissions "
                "issues or API not enabled. Skipping sync to preserve existing data.",
                project_id,
            )
            return None
        raise


def transform_datasets(datasets_data: list[dict], project_id: str) -> list[dict]:
    transformed: list[dict] = []
    for dataset in datasets_data:
        ref = dataset.get("datasetReference", {})
        dataset_id = ref.get("datasetId", "")
        transformed.append({
            "id": f"{project_id}:{dataset_id}",
            "dataset_id": dataset_id,
            "friendly_name": dataset.get("friendlyName"),
            "description": dataset.get("description"),
            "location": dataset.get("location"),
            "creation_time": dataset.get("creationTime"),
            "last_modified_time": dataset.get("lastModifiedTime"),
            "default_table_expiration_ms": dataset.get("defaultTableExpirationMs"),
            "default_partition_expiration_ms": dataset.get("defaultPartitionExpirationMs"),
            "project_id": project_id,
        })
    return transformed


@timeit
def load_bigquery_datasets(
    neo4j_session: neo4j.Session,
    data: list[dict],
    project_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        GCPBigQueryDatasetSchema(),
        data,
        lastupdated=update_tag,
        PROJECT_ID=project_id,
    )


@timeit
def cleanup_bigquery_datasets(
    neo4j_session: neo4j.Session, common_job_parameters: dict,
) -> None:
    GraphJob.from_node_schema(GCPBigQueryDatasetSchema(), common_job_parameters).run(
        neo4j_session,
    )


@timeit
def sync_bigquery_datasets(
    neo4j_session: neo4j.Session,
    client: Resource,
    project_id: str,
    update_tag: int,
    common_job_parameters: dict,
) -> list[dict] | None:
    logger.info("Syncing BigQuery datasets for project %s.", project_id)
    datasets_raw = get_bigquery_datasets(client, project_id)

    if datasets_raw is not None:
        datasets = transform_datasets(datasets_raw, project_id)
        load_bigquery_datasets(neo4j_session, datasets, project_id, update_tag)

        cleanup_job_params = common_job_parameters.copy()
        cleanup_job_params["PROJECT_ID"] = project_id
        cleanup_bigquery_datasets(neo4j_session, cleanup_job_params)

    return datasets_raw
