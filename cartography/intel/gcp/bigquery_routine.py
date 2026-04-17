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


def _normalize_connection_id(connection_id: str | None) -> str | None:
    """
    Normalize a BigQuery connection ID to the full resource name format.

    The API may return connection IDs in either short form
    (``project_number.location.connection_name``) or full resource name form
    (``projects/…/locations/…/connections/…``).  This function ensures we
    always store the full resource name so that relationship matching works.
    """
    if connection_id is None:
        return None
    if connection_id.startswith("projects/"):
        return connection_id
    parts = connection_id.split(".")
    if len(parts) == 3:
        return f"projects/{parts[0]}/locations/{parts[1]}/connections/{parts[2]}"
    return connection_id


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
        if is_api_disabled_error(e) or e.resp.status in (403, 404):
            logger.warning(
                "Could not retrieve BigQuery routines for dataset %s:%s - %s. Skipping.",
                project_id,
                dataset_id,
                e,
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
        ref = routine["routineReference"]
        routine_id = ref["routineId"]
        remote_opts = routine.get("remoteFunctionOptions", {}) or {}
        transformed.append(
            {
                "id": f"{dataset_full_id}.{routine_id}",
                "routine_id": routine_id,
                "dataset_id": dataset_full_id,
                "routine_type": routine.get("routineType"),
                "language": routine.get("language"),
                "creation_time": routine.get("creationTime"),
                "last_modified_time": routine.get("lastModifiedTime"),
                "connection_id": _normalize_connection_id(
                    remote_opts.get("connection")
                ),
            },
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
        ref = dataset["datasetReference"]
        dataset_id = ref["datasetId"]
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
