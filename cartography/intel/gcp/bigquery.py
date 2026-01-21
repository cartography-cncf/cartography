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
from cartography.models.gcp.bigquery_dataset import GCPBigQueryDatasetSchema
from cartography.models.gcp.bigquery_table import GCPBigQueryTableSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_client(project_id: str, credentials: Optional[GoogleCredentials] = None) -> bigquery.Client:
    """
    Returns a BigQuery client for the given project.
    """
    return bigquery.Client(project=project_id, credentials=credentials)


@timeit
def get_datasets(client: bigquery.Client, project_id: str) -> List[Any]:
    """
    Fetches a list of dataset objects from the BigQuery project.
    """
    datasets = []
    try:
        for dataset_list_item in client.list_datasets():
            
            dataset = client.get_dataset(dataset_list_item.reference)
            datasets.append(dataset)
    except Exception as e:
        logger.error(f"Failed to list datasets for project {project_id}: {e}")
       
        raise
    return datasets


@timeit
def transform_datasets(bq_datasets: List[Any], project_id: str) -> List[Dict[str, Any]]:
    """
    Transforms BigQuery Dataset objects into dictionaries for Neo4j loading.
    """
    results = []
    for dataset in bq_datasets:
        results.append({
            "id": dataset.full_dataset_id,
            "dataset_id": dataset.dataset_id,
            "project_id": project_id,
            "location": dataset.location,
            "friendly_name": dataset.friendly_name,
            "description": dataset.description,
            "created": dataset.created,
            "modified": dataset.modified,
        })
    return results


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
def get_tables(client: bigquery.Client, dataset_id: str) -> List[Any]:
    """
    Fetches table objects for a specific dataset.
    """
    tables = []
    try:
        dataset_ref = client.dataset(dataset_id)
        for table in client.list_tables(dataset_ref):
            tables.append(table)
    except Exception as e:
        logger.error(f"Failed to list tables for dataset {dataset_id}: {e}")
    return tables


@timeit
def transform_tables(bq_tables: List[Any], project_id: str, dataset_full_id: str) -> List[Dict[str, Any]]:
    """
    Transforms BigQuery Table objects into dictionaries for Neo4j loading.
    """
    results = []
    for table in bq_tables:
        uid = f"{dataset_full_id}.{table.table_id}"
        
        results.append({
            "id": uid,
            "table_id": table.table_id,
            "dataset_full_id": dataset_full_id,
            "project_id": project_id,
            "type": table.table_type,
            "creation_time": table.created,
            "expires": table.expires,
        })
    return results


@timeit
def load_tables(
    neo4j_session: neo4j.Session,
    data_list: List[Dict[str, Any]],
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

    bq_datasets = get_datasets(client, project_id)
    transformed_datasets = transform_datasets(bq_datasets, project_id)
    
    if transformed_datasets:
        logger.info(f"Loading {len(transformed_datasets)} datasets for project {project_id}.")
        load_datasets(neo4j_session, transformed_datasets, project_id, gcp_update_tag)

        all_tables = []
        for dataset in transformed_datasets:
            dataset_full_id = dataset['id']
            simple_ds_id = dataset['dataset_id']
            
            bq_tables = get_tables(client, simple_ds_id)
            transformed_tables = transform_tables(bq_tables, project_id, dataset_full_id)
            all_tables.extend(transformed_tables)
        
        if all_tables:
            logger.info(f"Loading {len(all_tables)} tables for project {project_id}.")
            load_tables(neo4j_session, all_tables, gcp_update_tag)
    else:
        logger.info(f"No datasets found for project {project_id}.")

    cleanup_tables(neo4j_session, common_job_parameters)
    cleanup_datasets(neo4j_session, common_job_parameters)
