import logging
import threading
from concurrent.futures import as_completed
from concurrent.futures import ThreadPoolExecutor

import neo4j
from google.api_core.exceptions import Forbidden
from google.api_core.exceptions import NotFound
from google.auth.credentials import Credentials as GoogleCredentials
from google.cloud.bigquery import Client
from google.cloud.bigquery.dataset import DatasetListItem

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.gcp.clients import build_bigquery_client
from cartography.models.gcp.bigquery.dataset import GCPBigQueryDatasetSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

_DEFAULT_BIGQUERY_DATASET_DETAIL_WORKERS = 10


@timeit
def get_bigquery_datasets(
    client: Client,
    project_id: str,
    credentials: GoogleCredentials | None = None,
    max_workers: int = _DEFAULT_BIGQUERY_DATASET_DETAIL_WORKERS,
) -> list[dict] | None:
    """
    Gets BigQuery datasets for a project.

    Returns:
        list[dict]: List of BigQuery datasets (empty list if project has no datasets)
        None: If the BigQuery API is not enabled or access is denied

    Raises:
        HttpError: For errors other than API disabled or permission denied
    """
    try:
        dataset_items = list(client.list_datasets(project=project_id, include_all=True))
    except (Forbidden, NotFound) as e:
        logger.warning(
            "Could not retrieve BigQuery datasets on project %s - %s. "
            "Skipping sync to preserve existing data.",
            project_id,
            e,
        )
        return None

    if not dataset_items:
        return []

    def _get_dataset_id(dataset_item: DatasetListItem) -> str:
        return f"{dataset_item.project}.{dataset_item.dataset_id}"

    def _fetch_dataset_detail(dataset_ref: str) -> dict | None:
        try:
            return client.get_dataset(dataset_ref).to_api_repr()
        except (Forbidden, NotFound) as e:
            logger.warning(
                "Could not retrieve BigQuery dataset detail for %s - %s. Skipping.",
                dataset_ref,
                e,
            )
            return None

    if len(dataset_items) < 2 or max_workers <= 1 or credentials is None:
        datasets: list[dict] = []
        for dataset_item in dataset_items:
            detail = _fetch_dataset_detail(_get_dataset_id(dataset_item))
            if detail is not None:
                datasets.append(detail)
        return datasets

    thread_local = threading.local()

    def _get_thread_client() -> Client:
        thread_client = getattr(thread_local, "client", None)
        if thread_client is None:
            thread_client = build_bigquery_client(credentials=credentials)
            thread_local.client = thread_client
        return thread_client

    def _fetch_dataset_detail_threaded(dataset_ref: str) -> dict | None:
        try:
            return _get_thread_client().get_dataset(dataset_ref).to_api_repr()
        except (Forbidden, NotFound) as e:
            logger.warning(
                "Could not retrieve BigQuery dataset detail for %s - %s. Skipping.",
                dataset_ref,
                e,
            )
            return None

    datasets = []
    dataset_refs = [_get_dataset_id(dataset_item) for dataset_item in dataset_items]
    with ThreadPoolExecutor(
        max_workers=min(max_workers, len(dataset_refs))
    ) as executor:
        futures = {
            executor.submit(_fetch_dataset_detail_threaded, dataset_ref): dataset_ref
            for dataset_ref in dataset_refs
        }
        for future in as_completed(futures):
            detail = future.result()
            if detail is not None:
                datasets.append(detail)

    return datasets


def transform_datasets(datasets_data: list[dict], project_id: str) -> list[dict]:
    transformed: list[dict] = []
    for dataset in datasets_data:
        ref = dataset["datasetReference"]
        dataset_id = ref["datasetId"]
        transformed.append(
            {
                "id": f"{project_id}:{dataset_id}",
                "dataset_id": dataset_id,
                "friendly_name": dataset.get("friendlyName"),
                "description": dataset.get("description"),
                "location": dataset.get("location"),
                "creation_time": dataset.get("creationTime"),
                "last_modified_time": dataset.get("lastModifiedTime"),
                "default_table_expiration_ms": dataset.get("defaultTableExpirationMs"),
                "default_partition_expiration_ms": dataset.get(
                    "defaultPartitionExpirationMs"
                ),
                "project_id": project_id,
            }
        )
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
    neo4j_session: neo4j.Session,
    common_job_parameters: dict,
) -> None:
    GraphJob.from_node_schema(GCPBigQueryDatasetSchema(), common_job_parameters).run(
        neo4j_session,
    )


@timeit
def sync_bigquery_datasets(
    neo4j_session: neo4j.Session,
    client: Client,
    project_id: str,
    update_tag: int,
    common_job_parameters: dict,
    credentials: GoogleCredentials | None = None,
) -> list[dict] | None:
    logger.info("Syncing BigQuery datasets for project %s.", project_id)
    datasets_raw = get_bigquery_datasets(
        client,
        project_id,
        credentials=credentials,
    )

    if datasets_raw is not None:
        datasets = transform_datasets(datasets_raw, project_id)
        load_bigquery_datasets(neo4j_session, datasets, project_id, update_tag)

        cleanup_job_params = common_job_parameters.copy()
        cleanup_job_params["PROJECT_ID"] = project_id
        cleanup_bigquery_datasets(neo4j_session, cleanup_job_params)

    return datasets_raw
