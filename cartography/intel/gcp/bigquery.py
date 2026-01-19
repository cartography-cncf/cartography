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
            # Fetch full dataset details to get all properties
            dataset = client.get_dataset(dataset_list_item.reference)
            datasets.append(dataset)
    except Exception as e:
        logger.error(f"Failed to list datasets for project {project_id}: {e}")
        # Re-raise the exception to prevent partial syncs from triggering cleanup
        raise
    return datasets


@timeit
def transform_datasets(bq_datasets: List[Any], project_id: str) -> List[Dict[str, Any]]:
    """
    Transforms BigQuery Dataset objects into dictionaries for Neo4j loading.
    """
    results = []
    for dataset in bq_datasets:
        # GCP Dataset IDs are unique per project. We construct a global ID by prepending the project ID.
        uid = f"{project_id}.{dataset.dataset_id}"
        
        results.append({
            "id": uid,
            "dataset_id": dataset.dataset_id,
            "project_id": project_id,
            "location": dataset.location,
            "friendly_name": dataset.friendly_name,
            "full_dataset_id": dataset.full_dataset_id,
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
        # We continue here to allow other datasets to sync even if one fails
    return tables


@timeit
def transform_tables(bq_tables: List[Any], project_id: str, dataset_id: str) -> List[Dict[str, Any]]:
    """
    Transforms BigQuery Table objects into dictionaries for Neo4j loading.
    """
    results = []
    for table in bq_tables:
        # Construct global ID: project_id.dataset_id.table_id
        uid = f"{project_id}.{dataset_id}.{table.table_id}"
        
        results.append({
            "id": uid,
            "table_id": table.table_id,
            "dataset_id": f"{project_id}.{dataset_id}",
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
    # Tables are cleaned up per project, not per dataset
    cleanup_query = """
        MATCH (t:GCPBigQueryTable)<-[:CONTAINS]-(d:GCPBigQueryDataset)<-[:RESOURCE]-(p:GCPProject{id: $PROJECT_ID})
        WHERE t.lastupdated <> $UPDATE_TAG
        WITH t LIMIT $LIMIT_SIZE
        DETACH DELETE t
    """
    neo4j_session.run(
        cleanup_query,
        PROJECT_ID=common_job_parameters["PROJECT_ID"],
        UPDATE_TAG=common_job_parameters["UPDATE_TAG"],
        LIMIT_SIZE=100,
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
    bq_datasets = get_datasets(client, project_id)
    transformed_datasets = transform_datasets(bq_datasets, project_id)
    
    if transformed_datasets:
        logger.info(f"Loading {len(transformed_datasets)} datasets for project {project_id}.")
        load_datasets(neo4j_session, transformed_datasets, project_id, gcp_update_tag)

        # 2. Sync Tables for each Dataset
        for dataset in transformed_datasets:
            ds_id = dataset['dataset_id']
            dataset_node_id = dataset['id']
            
            bq_tables = get_tables(client, ds_id)
            transformed_tables = transform_tables(bq_tables, project_id, ds_id)
            
            if transformed_tables:
                logger.info(f"Loading {len(transformed_tables)} tables for dataset {ds_id}.")
                load_tables(neo4j_session, transformed_tables, dataset_node_id, gcp_update_tag)
    else:
        logger.info(f"No datasets found for project {project_id}.")

    # 3. Cleanup stale data
    cleanup_tables(neo4j_session, common_job_parameters)
    cleanup_datasets(neo4j_session, common_job_parameters)
