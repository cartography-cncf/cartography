import logging

import neo4j
from googleapiclient.discovery import Resource
from googleapiclient.errors import HttpError

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.gcp.util import gcp_api_execute_with_retry
from cartography.intel.gcp.util import is_api_disabled_error
from cartography.models.gcp.bigquery.routine import GCPBigQueryRoutineSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_bigquery_routines(
    client: Resource,
    project_id: str,
    dataset_id: str,
) -> list[dict] | None:
    """
    Gets BigQuery routines for a dataset.

    Returns:
        list[dict]: List of BigQuery routines (empty list if dataset has no routines)
        None: If the BigQuery API is not enabled or access is denied

    Raises:
        HttpError: For errors other than API disabled or permission denied
    """
    try:
        routines: list[dict] = []
        request = client.routines().list(projectId=project_id, datasetId=dataset_id)
        while request is not None:
            response = gcp_api_execute_with_retry(request)
            routines.extend(response.get("routines", []))
            request = client.routines().list_next(
                previous_request=request,
                previous_response=response,
            )
        return routines
    except HttpError as e:
        if is_api_disabled_error(e):
            logger.warning(
                "Could not retrieve BigQuery routines for dataset %s:%s due to permissions "
                "issues or API not enabled. Skipping.",
                project_id,
                dataset_id,
            )
            return None
        raise


def transform_routines(
    routines_data: list[dict],
    project_id: str,
    dataset_full_id: str,
) -> list[dict]:
    transformed: list[dict] = []
    for routine in routines_data:
        ref = routine.get("routineReference", {})
        routine_id = ref.get("routineId", "")
        transformed.append(
            {
                "id": f"{dataset_full_id}.{routine_id}",
                "routine_id": routine_id,
                "dataset_id": dataset_full_id,
                "routine_type": routine.get("routineType"),
                "language": routine.get("language"),
                "creation_time": routine.get("creationTime"),
                "last_modified_time": routine.get("lastModifiedTime"),
            }
        )
    return transformed


@timeit
def load_bigquery_routines(
    neo4j_session: neo4j.Session,
    data: list[dict],
    project_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        GCPBigQueryRoutineSchema(),
        data,
        lastupdated=update_tag,
        PROJECT_ID=project_id,
    )


@timeit
def cleanup_bigquery_routines(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict,
) -> None:
    GraphJob.from_node_schema(GCPBigQueryRoutineSchema(), common_job_parameters).run(
        neo4j_session,
    )


@timeit
def sync_bigquery_routines(
    neo4j_session: neo4j.Session,
    client: Resource,
    datasets: list[dict],
    project_id: str,
    update_tag: int,
    common_job_parameters: dict,
) -> None:
    logger.info("Syncing BigQuery routines for project %s.", project_id)
    all_routines_transformed: list[dict] = []

    for dataset in datasets:
        ref = dataset.get("datasetReference", {})
        dataset_id = ref.get("datasetId", "")
        dataset_full_id = f"{project_id}:{dataset_id}"

        routines_raw = get_bigquery_routines(client, project_id, dataset_id)
        if routines_raw is not None:
            all_routines_transformed.extend(
                transform_routines(routines_raw, project_id, dataset_full_id),
            )

    load_bigquery_routines(
        neo4j_session,
        all_routines_transformed,
        project_id,
        update_tag,
    )

    cleanup_job_params = common_job_parameters.copy()
    cleanup_job_params["PROJECT_ID"] = project_id
    cleanup_bigquery_routines(neo4j_session, cleanup_job_params)
