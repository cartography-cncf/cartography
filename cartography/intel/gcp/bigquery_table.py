import logging
import threading
from concurrent.futures import as_completed
from concurrent.futures import ThreadPoolExecutor

import neo4j
from google.api_core.exceptions import Forbidden
from google.api_core.exceptions import NotFound
from google.auth.credentials import Credentials as GoogleCredentials
from google.cloud.bigquery import Client

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.gcp.clients import build_bigquery_client
from cartography.models.gcp.bigquery.table import GCPBigQueryTableSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

_DEFAULT_BIGQUERY_TABLE_DETAIL_WORKERS = 10


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
def get_bigquery_tables(
    client: Client,
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
        dataset_ref = f"{project_id}.{dataset_id}"
        return [table.to_api_repr() for table in client.list_tables(dataset_ref)]
    except (Forbidden, NotFound) as e:
        logger.warning(
            "Could not retrieve BigQuery tables for dataset %s:%s - %s. Skipping.",
            project_id,
            dataset_id,
            e,
        )
        return None


@timeit
def get_bigquery_table_detail(
    client: Client,
    project_id: str,
    dataset_id: str,
    table_id: str,
) -> dict | None:
    """
    Gets full details for a single BigQuery table via tables.get.

    tables.list does not return numBytes, numRows, numLongTermBytes, description,
    friendlyName, or externalDataConfiguration. We call tables.get per table to
    retrieve these fields.

    Returns:
        dict: The full table resource
        None: If the table could not be retrieved

    """
    try:
        table_ref = f"{project_id}.{dataset_id}.{table_id}"
        return client.get_table(table_ref).to_api_repr()
    except (Forbidden, NotFound) as e:
        logger.warning(
            "Could not retrieve BigQuery table detail for %s:%s.%s - %s. Skipping.",
            project_id,
            dataset_id,
            table_id,
            e,
        )
        return None


def transform_tables(
    tables_data: list[dict],
    project_id: str,
    dataset_full_id: str,
) -> list[dict]:
    transformed: list[dict] = []
    for table in tables_data:
        ref = table["tableReference"]
        table_id = ref["tableId"]
        ext_config = table.get("externalDataConfiguration", {}) or {}
        connection_id = _normalize_connection_id(ext_config.get("connectionId"))
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
                "description": table.get("description"),
                "friendly_name": table.get("friendlyName"),
                "connection_id": connection_id,
            },
        )
    return transformed


def _enrich_bigquery_tables_with_details(
    client: Client,
    project_id: str,
    dataset_id: str,
    tables_raw: list[dict],
    credentials: GoogleCredentials | None = None,
    max_workers: int = _DEFAULT_BIGQUERY_TABLE_DETAIL_WORKERS,
) -> None:
    if len(tables_raw) < 2 or max_workers <= 1:
        for table in tables_raw:
            table_ref = table["tableReference"]
            detail = get_bigquery_table_detail(
                client,
                project_id,
                dataset_id,
                table_ref["tableId"],
            )
            if detail is not None:
                table.update(detail)
        return

    if credentials is None:
        logger.debug(
            "BigQuery table detail enrichment for %s:%s is falling back to sequential fetches because no credentials were provided for thread-local clients.",
            project_id,
            dataset_id,
        )
        for table in tables_raw:
            table_ref = table["tableReference"]
            detail = get_bigquery_table_detail(
                client,
                project_id,
                dataset_id,
                table_ref["tableId"],
            )
            if detail is not None:
                table.update(detail)
        return

    thread_local = threading.local()

    def _get_thread_client() -> Client:
        thread_client = getattr(thread_local, "client", None)
        if thread_client is None:
            thread_client = build_bigquery_client(credentials=credentials)
            thread_local.client = thread_client
        return thread_client

    def _fetch_table_detail(index: int, table_id: str) -> tuple[int, dict | None]:
        detail = get_bigquery_table_detail(
            _get_thread_client(),
            project_id,
            dataset_id,
            table_id,
        )
        return index, detail

    max_parallelism = min(max_workers, len(tables_raw))
    with ThreadPoolExecutor(max_workers=max_parallelism) as executor:
        future_to_index = {
            executor.submit(
                _fetch_table_detail,
                index,
                table["tableReference"]["tableId"],
            ): index
            for index, table in enumerate(tables_raw)
        }
        for completed, future in enumerate(as_completed(future_to_index), start=1):
            index, detail = future.result()
            if detail is not None:
                tables_raw[index].update(detail)
            if completed % 100 == 0 or completed == len(tables_raw):
                logger.debug(
                    "Fetched details for %d/%d tables in dataset %s:%s.",
                    completed,
                    len(tables_raw),
                    project_id,
                    dataset_id,
                )


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
    client: Client,
    datasets: list[dict],
    project_id: str,
    update_tag: int,
    common_job_parameters: dict,
    credentials: GoogleCredentials | None = None,
) -> None:
    logger.info("Syncing BigQuery tables for project %s.", project_id)
    all_tables_raw: list[tuple[list[dict], str]] = []

    for dataset in datasets:
        ref = dataset["datasetReference"]
        dataset_id = ref["datasetId"]

        tables_raw = get_bigquery_tables(client, project_id, dataset_id)
        if tables_raw is not None:
            _enrich_bigquery_tables_with_details(
                client,
                project_id,
                dataset_id,
                tables_raw,
                credentials=credentials,
            )
            all_tables_raw.append((tables_raw, dataset_id))

    all_tables_transformed: list[dict] = []
    for raw_tables, ds_id in all_tables_raw:
        dataset_full_id = f"{project_id}:{ds_id}"
        all_tables_transformed.extend(
            transform_tables(raw_tables, project_id, dataset_full_id),
        )

    load_bigquery_tables(neo4j_session, all_tables_transformed, project_id, update_tag)

    cleanup_job_params = common_job_parameters.copy()
    cleanup_job_params["PROJECT_ID"] = project_id
    cleanup_bigquery_tables(neo4j_session, cleanup_job_params)
