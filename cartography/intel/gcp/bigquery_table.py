import logging

import neo4j
from googleapiclient.discovery import Resource
from googleapiclient.errors import HttpError

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.gcp.util import gcp_api_execute_with_retry
from cartography.intel.gcp.util import is_api_disabled_error
from cartography.models.gcp.bigquery.table import GCPBigQueryTableSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_bigquery_tables(
    client: Resource,
    project_id: str,
    dataset_id: str,
) -> list[dict] | None:
    """
    Gets BigQuery tables for a dataset.

    Returns:
        list[dict]: List of BigQuery tables (empty list if dataset has no tables)
        None: If the BigQuery API is not enabled or access is denied

    Raises:
        HttpError: For errors other than API disabled or permission denied
    """
    try:
        tables: list[dict] = []
        request = client.tables().list(projectId=project_id, datasetId=dataset_id)
        while request is not None:
            response = gcp_api_execute_with_retry(request)
            tables.extend(response.get("tables", []))
            request = client.tables().list_next(
                previous_request=request,
                previous_response=response,
            )
        return tables
    except HttpError as e:
        if is_api_disabled_error(e):
            logger.warning(
                "Could not retrieve BigQuery tables for dataset %s:%s due to permissions "
                "issues or API not enabled. Skipping.",
                project_id,
                dataset_id,
            )
            return None
        raise


def transform_tables(
    tables_data: list[dict],
    project_id: str,
    dataset_full_id: str,
) -> list[dict]:
    transformed: list[dict] = []
    for table in tables_data:
        ref = table.get("tableReference", {})
        table_id = ref.get("tableId", "")
        transformed.append(
            {
                "id": f"{dataset_full_id}.{table_id}",
                "table_id": table_id,
                "dataset_id": dataset_full_id,
                "type": table.get("type"),
                "creation_time": table.get("creationTime"),
                "expiration_time": table.get("expirationTime"),
                "num_bytes": table.get("numBytes"),
                "num_long_term_bytes": table.get("numLongTermBytes"),
                "num_rows": table.get("numRows"),
            }
        )
    return transformed


@timeit
def load_bigquery_tables(
    neo4j_session: neo4j.Session,
    data: list[dict],
    project_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        GCPBigQueryTableSchema(),
        data,
        lastupdated=update_tag,
        PROJECT_ID=project_id,
    )


@timeit
def cleanup_bigquery_tables(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict,
) -> None:
    GraphJob.from_node_schema(GCPBigQueryTableSchema(), common_job_parameters).run(
        neo4j_session,
    )


@timeit
def sync_bigquery_tables(
    neo4j_session: neo4j.Session,
    client: Resource,
    datasets: list[dict],
    project_id: str,
    update_tag: int,
    common_job_parameters: dict,
) -> None:
    logger.info("Syncing BigQuery tables for project %s.", project_id)
    all_tables_transformed: list[dict] = []

    for dataset in datasets:
        ref = dataset.get("datasetReference", {})
        dataset_id = ref.get("datasetId", "")
        dataset_full_id = f"{project_id}:{dataset_id}"

        tables_raw = get_bigquery_tables(client, project_id, dataset_id)
        if tables_raw is not None:
            all_tables_transformed.extend(
                transform_tables(tables_raw, project_id, dataset_full_id),
            )

    load_bigquery_tables(neo4j_session, all_tables_transformed, project_id, update_tag)

    cleanup_job_params = common_job_parameters.copy()
    cleanup_job_params["PROJECT_ID"] = project_id
    cleanup_bigquery_tables(neo4j_session, cleanup_job_params)
