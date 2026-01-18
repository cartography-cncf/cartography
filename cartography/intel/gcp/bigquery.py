import logging
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

import neo4j
from google.auth.credentials import Credentials as GoogleCredentials
from google.cloud import bigquery

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.gcp.bigquery import GCPBigQueryDatasetSchema
from cartography.models.gcp.bigquery import GCPBigQueryTableSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_client(project_id: str, credentials: Optional[GoogleCredentials] = None) -> bigquery.Client:
    """
    Returns a BigQuery client for the given project.
    """
    return bigquery.Client(project=project_id, credentials=credentials)


@timeit
def get_datasets(client: bigquery.Client, project_id: str) -> List[Dict[str, Any]]:
    """
    Fetches a list of datasets from the BigQuery project.
    """
    datasets = []
    try:
        for dataset_list_item in client.list_datasets():
            # Fetch full dataset details
            dataset = client.get_dataset(dataset_list_item.reference)
            datasets.append({
                "id": f"{project_id}.{dataset.dataset_id}",
                "dataset_id": dataset.dataset_id,
                "project_id": project_id,
                "location": dataset.location,
                "friendly_name": dataset.friendly_name or dataset.dataset_id,
                "full_dataset_id": dataset_list_item.full_dataset_id,
                "description": dataset.description,
                # Convert dates to strings to ensure JSON serialization compatibility if needed,
                # though Neo4j driver often handles datetime objects.
                "created": str(dataset.created) if dataset.created else None,
                "modified": str(dataset.modified) if dataset.modified else None,
            })
    except Exception as e:
        logger.error(f"Failed to list datasets for project {project_id}: {e}")
        # Re-raise the exception to prevent partial syncs from triggering cleanup
        raise
    return datasets


@timeit
def load_datasets(
    neo4j_session: neo4j.Session,
    data_list: List[Dict[str, Any]],
    project_id: str,
    update_tag: int,
) -> None:
    """
    Ingest BigQuery Datasets into Neo4j using the Cartography load() function.
    """
    load(
        neo4j_session,
        GCPBigQueryDatasetSchema(),
        data_list,
        lastupdated=update_tag,
        PROJECT_ID=project_id,
    )


@timeit
def get_tables(client: bigquery.Client, dataset_id: str, project_id: str) -> List[Dict[str, Any]]:
    """
    Fetches tables for a specific dataset.
    """
    tables = []
    try:
        dataset_ref = client.dataset(dataset_id)
        for table in client.list_tables(dataset_ref):
            tables.append({
                "id": f"{project_id}.{dataset_id}.{table.table_id}",
                "table_id": table.table_id,
                "dataset_id": f"{project_id}.{dataset_id}",  # This ID must match the parent dataset node ID
                "project_id": project_id,
                "type": table.table_type,
                "creation_time": str(table.created) if table.created else None,
                "expires": str(table.expires) if table.expires else None,
            })
    except Exception as e:
        logger.error(f"Failed to list tables for dataset {dataset_id}: {e}")
        # We prefer to log error here but continue to other datasets
    return tables


@timeit
def load_tables(
    neo4j_session: neo4j.Session,
    data_list: List[Dict[str, Any]],
    dataset_node_id: str,
    update_tag: int,
) -> None:
    """
    Ingest BigQuery Tables into Neo4j using the Cartography load() function.
    """
    load(
        neo4j_session,
        GCPBigQueryTableSchema(),
        data_list,
        lastupdated=update_tag,
        DATASET_ID=dataset_node_id,
    )


@timeit
def cleanup_datasets(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict[str, Any],
) -> None:
    """
    Delete stale BigQuery Dataset resources.
    """
    GraphJob.from_node_schema(GCPBigQueryDatasetSchema(), common_job_parameters).run(
        neo4j_session,
    )


@timeit
def cleanup_tables(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict[str, Any],
) -> None:
    """
    Delete stale BigQuery Table resources.
    """
    GraphJob.from_node_schema(GCPBigQueryTableSchema(), common_job_parameters).run(
        neo4j_session,
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    project_id: str,
    gcp_update_tag: int,
    credentials: Optional[GoogleCredentials],
    common_job_parameters: Dict[str, Any],
) -> None:
    """
    Main BigQuery Sync Function.
    Syncs BigQuery datasets and tables for a given GCP project.
    """
    logger.info(f"Syncing BigQuery for project {project_id}...")
    client = get_client(project_id, credentials)

    # 1. Sync Datasets
    datasets = get_datasets(client, project_id)
    if datasets:
        logger.info(f"Loading {len(datasets)} datasets for project {project_id}.")
        load_datasets(neo4j_session, datasets, project_id, gcp_update_tag)

        # 2. Sync Tables for each Dataset
        for dataset in datasets:
            ds_id = dataset['dataset_id']
            # The 'id' field in the dataset dict corresponds to the graph node ID
            dataset_node_id = dataset['id']

            tables = get_tables(client, ds_id, project_id)
            if tables:
                logger.info(f"Loading {len(tables)} tables for dataset {ds_id}.")
                load_tables(neo4j_session, tables, dataset_node_id, gcp_update_tag)
    else:
        logger.info(f"No datasets found for project {project_id}.")

    # 3. Cleanup stale data
    cleanup_tables(neo4j_session, common_job_parameters)
    cleanup_datasets(neo4j_session, common_job_parameters)
