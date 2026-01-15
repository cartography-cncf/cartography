import logging
from typing import Any
from typing import Dict
from typing import List

import neo4j
from google.cloud import bigquery

from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_client(project_id: str) -> bigquery.Client:
    """
    Returns a BigQuery client for the given project.
    """
    return bigquery.Client(project=project_id)


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
                "created": str(dataset.created) if dataset.created else None,
                "modified": str(dataset.modified) if dataset.modified else None,
            })
    except Exception as e:
        logger.error(f"Failed to list datasets for project {project_id}: {e}")
    return datasets


@timeit
def load_datasets(
    neo4j_session: neo4j.Session,
    data_list: List[Dict[str, Any]],
    project_id: str,
    update_tag: int,
) -> None:
    """
    Ingest BigQuery Datasets into Neo4j and link them to the GCPProject.
    """
    ingest_query = """
    UNWIND $Datasets as dataset
    MERGE (d:GCPBigQueryDataset {id: dataset.id})
    ON CREATE SET d.firstseen = timestamp(), d.created_at = timestamp()
    SET d.lastupdated = $UpdateTag,
        d.dataset_id = dataset.dataset_id,
        d.project_id = dataset.project_id,
        d.location = dataset.location,
        d.friendly_name = dataset.friendly_name,
        d.full_dataset_id = dataset.full_dataset_id,
        d.description = dataset.description,
        d.created = dataset.created,
        d.modified = dataset.modified

    WITH d
    MATCH (p:GCPProject {id: $ProjectId})
    MERGE (p)-[r:RESOURCE]->(d)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $UpdateTag
    """
    neo4j_session.run(
        ingest_query,
        Datasets=data_list,
        ProjectId=project_id,
        UpdateTag=update_tag,
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
                "dataset_id": dataset_id,
                "project_id": project_id,
                "type": table.table_type,
                "creation_time": str(table.created) if table.created else None,
                "expires": str(table.expires) if table.expires else None,
            })
    except Exception as e:
        logger.error(f"Failed to list tables for dataset {dataset_id}: {e}")
    return tables


@timeit
def load_tables(
    neo4j_session: neo4j.Session,
    data_list: List[Dict[str, Any]],
    dataset_id: str,
    project_id: str,
    update_tag: int,
) -> None:
    """
    Ingest BigQuery Tables into Neo4j and link them to their parent Dataset.
    """
    ingest_query = """
    UNWIND $Tables as table
    MERGE (t:GCPBigQueryTable {id: table.id})
    ON CREATE SET t.firstseen = timestamp(), t.created_at = timestamp()
    SET t.lastupdated = $UpdateTag,
        t.table_id = table.table_id,
        t.dataset_id = table.dataset_id,
        t.project_id = table.project_id,
        t.type = table.type,
        t.creation_time = table.creation_time,
        t.expires = table.expires

    WITH t
    MATCH (d:GCPBigQueryDataset {id: $DatasetNodeId})
    MERGE (d)-[r:CONTAINS]->(t)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $UpdateTag
    """
    dataset_node_id = f"{project_id}.{dataset_id}"
    
    neo4j_session.run(
        ingest_query,
        Tables=data_list,
        DatasetNodeId=dataset_node_id,
        UpdateTag=update_tag,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict[str, Any],
) -> None:
    """
    Delete stale BigQuery resources.
    """
    # Cleanup Tables first (children before parents)
    neo4j_session.run(
        """
        MATCH (t:GCPBigQueryTable)
        WHERE t.lastupdated <> $UPDATE_TAG
        WITH t LIMIT 1000
        DETACH DELETE t
        """,
        UPDATE_TAG=common_job_parameters['UPDATE_TAG'],
    )
    
    # Cleanup Datasets
    neo4j_session.run(
        """
        MATCH (d:GCPBigQueryDataset)
        WHERE d.lastupdated <> $UPDATE_TAG
        WITH d LIMIT 1000
        DETACH DELETE d
        """,
        UPDATE_TAG=common_job_parameters['UPDATE_TAG'],
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    project_id: str,
    gcp_update_tag: int,
    common_job_parameters: Dict[str, Any],
) -> None:
    """
    Main BigQuery Sync Function.
    Syncs BigQuery datasets and tables for a given GCP project.
    """
    logger.info(f"Syncing BigQuery for project {project_id}...")
    client = get_client(project_id)

    # 1. Sync Datasets
    datasets = get_datasets(client, project_id)
    if datasets:
        logger.info(f"Loading {len(datasets)} datasets for project {project_id}.")
        load_datasets(neo4j_session, datasets, project_id, gcp_update_tag)
        
        # 2. Sync Tables for each Dataset
        for dataset in datasets:
            ds_id = dataset['dataset_id']
            tables = get_tables(client, ds_id, project_id)
            if tables:
                logger.info(f"Loading {len(tables)} tables for dataset {ds_id}.")
                load_tables(neo4j_session, tables, ds_id, project_id, gcp_update_tag)
    else:
        logger.info(f"No datasets found for project {project_id}.")

    # 3. Cleanup stale data
    cleanup(neo4j_session, common_job_parameters)

