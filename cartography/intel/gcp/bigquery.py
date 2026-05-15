import json
import logging
import time
from typing import Dict
from typing import List

import neo4j
from cloudconsolelink.clouds.gcp import GCPLinker
from googleapiclient.discovery import HttpError
from googleapiclient.discovery import Resource

from . import label
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)
gcp_console_link = GCPLinker()


@timeit
def get_bigquery_dataset(bigquery: Resource, project_id: str, common_job_parameters) -> List[Resource]:
    """
    Returns a list of Bigquery Datasets within the given project.

    :type bigquery: The GCP Bigquery resource object
    :param bigquery: The Bigquery  resource object created by googleapiclient.discovery.build()

    :type project_id: str
    :param project_id: Current Google Project Id

    :rtype: list
    :return: List of Bigquery Datasets
    """
    try:
        datasets = []
        request = bigquery.datasets().list(projectId=project_id, maxResults=5000)
        while request is not None:
            response = request.execute()
            if 'datasets' in response:
                datasets.extend(response.get('datasets', []))
            request = bigquery.datasets().list_next(previous_request=request, previous_response=response)

        return datasets
    except HttpError as e:
        err = json.loads(e.content.decode('utf-8'))['error']
        if err.get('status', '') == 'PERMISSION_DENIED' or err.get('message', '') == 'Forbidden':
            logger.warning(
                (
                    "Could not retrieve Bigquery datasets on project %s due to permissions issues. Code: %s, Message: %s"
                ), project_id, err['code'], err['message'],
            )
            return []
        else:
            raise


@timeit
def transform_bigquery_dataset(bigquery: Resource, datasets: List[Dict], project_id: str) -> List[Resource]:
    list_dataset = []
    for dataset in datasets:
        dataset['id'] = dataset.get('datasetReference', {}).get('datasetId', '')
        dataset['uniqueId'] = f"projects/{project_id}/datasets/{dataset['id']}"
        dataset['details'] = get_dataset_info(bigquery, dataset['id'], project_id)
        dataset['consolelink'] = gcp_console_link.get_console_link(project_id=project_id, resource_name='bigquery_home')
        list_dataset.append(dataset)

    return list_dataset


@timeit
def get_dataset_info(bigquery, dataset_id, project_id):
    response = {}
    try:
        response = bigquery.datasets().get(projectId=project_id, datasetId=dataset_id).execute()

    except HttpError as e:
        err = json.loads(e.content.decode('utf-8'))['error']
        if err.get('status', '') == 'PERMISSION_DENIED' or err.get('message', '') == 'Forbidden':
            logger.warning(
                (
                    "Could not retrieve Bigquery dataset info on project %s due to permissions issues. Code: %s, Message: %s"
                ), project_id, err['code'], err['message'],
            )
            return {}
        else:
            raise

    return response


@timeit
def get_dataset_access_info(bigquery, dataset_id, project_id):
    response = {}
    try:
        response = bigquery.datasets().get(projectId=project_id, datasetId=dataset_id).execute()
        accesses = response.get('access', [])
    except HttpError as e:
        err = json.loads(e.content.decode('utf-8'))['error']
        if err.get('status', '') == 'PERMISSION_DENIED' or err.get('message', '') == 'Forbidden':
            logger.warning(
                (
                    "Could not retrieve Bigquery dataset info on project %s due to permissions issues. Code: %s, Message: %s"
                ), project_id, err['code'], err['message'],
            )
            return []
        else:
            raise

    return accesses


@timeit
def transform_dataset_accesses(response_objects: List[Dict], dataset_id: str, project_id: str) -> List[Dict]:
    """
    Process the GCP dataset access objects and return a flattened list of GCP accesses with all the necessary fields
    we need to load it into Neo4j
    :param response_objects: The return data from get_dataset_access_info()
    :return: A list of GCP GCP accesses
    """
    accesses_list = []
    for res in response_objects:
        res['id'] = f"projects/{project_id}/bigquery/{dataset_id}/role/{res['role']}"
        accesses_list.append(res)
    return accesses_list


@timeit
def attach_dataset_to_accesses(session: neo4j.Session, dataset_id: str, accesses: List[Dict], gcp_update_tag: int) -> None:
    session.execute_write(attach_dataset_to_accesses_tx, accesses, dataset_id, gcp_update_tag)


@timeit
def attach_dataset_to_accesses_tx(
    tx: neo4j.Transaction, accesses: List[Dict],
    dataset_id: str, gcp_update_tag: int,
) -> None:

    query = """
    UNWIND $Records as record
    MERGE (access:GCPAcl{id: record.id})
    ON CREATE SET
        access.firstseen = timestamp()
    SET
        access.lastupdated = $gcp_update_tag,
        access.special_group = record.specialGroup,
        access.role = record.role
    WITH access
    MATCH (dataset:GCPBigqueryDataset{id:$DatasetId})
    MERGE (dataset)<-[a:APPLIES_TO]-(access)
    ON CREATE SET
        a.firstseen = timestamp()
    SET a.lastupdated = $gcp_update_tag
    """
    tx.run(
        query,
        Records=accesses,
        DatasetId=dataset_id,
        gcp_update_tag=gcp_update_tag,
    )


@timeit
def get_bigquery_tables(bigquery: Resource, dataset: Dict, project_id: str, common_job_parameters) -> List[Resource]:
    """
    Returns a list of Bigquery Datasets  tables within the given project.

    :type datasets: The GCP Bigquery Dataset List
    :param datasets: The Bigquery Dataset List

    :type project_id: str
    :param project_id: Current Google Project Id

    :rtype: list
    :return: List of Bigquery Dataset tables
    """
    try:
        tables = []
        request = bigquery.tables().list(projectId=project_id, datasetId=dataset['id'], maxResults=5000)
        while request is not None:
            response = request.execute()
            if 'tables' in response:
                tables.extend(response.get('tables', []))
            request = bigquery.tables().list_next(previous_request=request, previous_response=response)
        return tables
    except HttpError as e:
        err = json.loads(e.content.decode('utf-8'))['error']
        if err.get('status', '') == 'PERMISSION_DENIED' or err.get('message', '') == 'Forbidden':
            logger.warning(
                (
                    "Could not retrieve Bigquery tables on project %s due to permissions issues. Code: %s, Message: %s"
                ), project_id, err['code'], err['message'],
            )
            return []
        else:
            raise


@timeit
def transform_bigquery_tables(bigquery: Resource, dataset: Dict, tables: List, project_id: str) -> List[Resource]:
    list_tables = []
    for table in tables:
        table['id'] = table.get('tableReference', {}).get('tableId', '')
        table['datasetId'] = dataset['id']
        table['uniqueId'] = f"projects/{project_id}/datasets/{dataset['id']}/tables/{table['id']}"
        table['details'] = get_table_info(bigquery, project_id, dataset['id'], table['id'])
        table['consolelink'] = gcp_console_link.get_console_link(project_id=project_id, resource_name='bigquery_home')
        list_tables.append(table)

    return list_tables


@timeit
def get_table_info(bigquery, project_id, dataset_id, table_id):
    response = {}
    try:
        response = bigquery.tables().get(projectId=project_id, datasetId=dataset_id, tableId=table_id).execute()

    except HttpError as e:
        err = json.loads(e.content.decode('utf-8'))['error']
        if err.get('status', '') == 'PERMISSION_DENIED' or err.get('message', '') == 'Forbidden':
            logger.warning(
                (
                    "Could not retrieve Bigquery table info on project %s due to permissions issues. Code: %s, Message: %s"
                ), project_id, err['code'], err['message'],
            )
            return {}
        else:
            raise

    return response


@timeit
def load_bigquery_datasets(session: neo4j.Session, datasets: List[Dict], project_id: str, update_tag: int) -> None:
    session.execute_write(load_bigquery_datasets_tx, datasets, project_id, update_tag)


@timeit
def load_bigquery_datasets_tx(
    tx: neo4j.Transaction, datasets: List[Dict],
    project_id: str, gcp_update_tag: int,
) -> None:
    query = """
    UNWIND $Datasets as d
    MERGE (dataset:GCPBigqueryDataset{id:d.id})
    ON CREATE SET
        dataset.firstseen = timestamp()
    SET
        dataset.lastseen = $gcp_update_tag,
        dataset.name = d.id,
        dataset.uniqueId = d.uniqueId,
        dataset.consolelink = d.consolelink,
        dataset.friendlyName = d.details.friendlyName,
        dataset.defaultTableExpirationMs = d.details.defaultTableExpirationMs,
        dataset.defaultPartitionExpirationMs = d.details.defaultPartitionExpirationMs,
        dataset.location = d.details.location,
        dataset.defaultCollation= d.details.defaultCollation,
        dataset.maxTimeTravelHours = d.details.maxTimeTravelHours
    WITH dataset
    MATCH (owner:GCPProject{id: $ProjectId})
    MERGE (owner)-[r:RESOURCE]->(dataset)
    ON CREATE SET
        r.firstseen = timestamp()
    SET r.lastupdated = $gcp_update_tag
    """
    tx.run(
        query,
        Datasets=datasets,
        ProjectId=project_id,
        gcp_update_tag=gcp_update_tag,
    )


@timeit
def load_bigquery_tables(session: neo4j.Session, tables: List[Dict], project_id: str, update_tag: int) -> None:
    session.execute_write(load_bigquery_tables_tx, tables, project_id, update_tag)


@timeit
def load_bigquery_tables_tx(
    tx: neo4j.Transaction, tables: List[Dict],
    project_id: str, gcp_update_tag: int,
) -> None:
    query = """
    UNWIND $Tables as t
    MERGE (table:GCPBigqueryTable{id:t.id})
    ON CREATE SET
        table.firstseen = timestamp()
    SET
        table.lastseen = $gcp_update_tag,
        table.name = t.id,
        table.uniqueId = t.uniqueId,
        table.consolelink = t.consolelink,
        table.friendlyName = t.details.friendlyName,
        table.requirePartitionFilter = t.details.requirePartitionFilter,
        table.numBytes = t.details.numBytes,
        table.numLongTermBytes = t.details.numLongTermBytes,
        table.numRows = t.details.numRows
    WITH table, t
    MATCH (dataset:GCPBigqueryDataset{id:t.datasetId})
    MERGE (dataset)-[r:HAS_TABLE]->(table)
    ON CREATE SET
        r.firstseen = timestamp()
    SET r.lastupdated = $gcp_update_tag
    """
    tx.run(
        query,
        Tables=tables,
        ProjectId=project_id,
        gcp_update_tag=gcp_update_tag,
    )


@timeit
def cleanup_gcp_bigquery(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    """
    Delete out-of-date GCP Bigquery and relationships

    :type neo4j_session: The Neo4j session object
    :param neo4j_session: The Neo4j session

    :type common_job_parameters: dict
    :param common_job_parameters: Dictionary of other job parameters to pass to Neo4j

    :rtype: NoneType
    :return: Nothing
    """
    run_cleanup_job('gcp_bigquery_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def cleanup_gcp_bigquery_accesses(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    """
    Delete out-of-date GCP Bigquery access and relationships

    :type neo4j_session: The Neo4j session object
    :param neo4j_session: The Neo4j session

    :type common_job_parameters: dict
    :param common_job_parameters: Dictionary of other job parameters to pass to Neo4j

    :rtype: NoneType
    :return: Nothing
    """
    run_cleanup_job('gcp_bigquery_access_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync(
    neo4j_session: neo4j.Session, bigquery: Resource, project_id: str, gcp_update_tag: int,
    common_job_parameters: Dict, regions: List,
) -> None:
    """
    Get GCP Bigquery using the Cloud Bigquery resource object, ingest to Neo4j, and clean up old data.

    :type neo4j_session: The Neo4j session object
    :param neo4j_session: The Neo4j session

    :type bigquery: The GCP Bigquery resource object created by googleapiclient.discovery.build()
    :param bigquery: The GCP Bigquery resource object

    :type project_id: str
    :param project_id: The project ID of the corresponding project

    :type gcp_update_tag: timestamp
    :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with

    :type common_job_parameters: dict
    :param common_job_parameters: Dictionary of other job parameters to pass to Neo4j

    :rtype: NoneType
    :return: Nothing
    """
    tic = time.perf_counter()

    logger.info("Syncing Bigquery for project '%s', at %s.", project_id, tic)

    # BIGQUERY DATASETS
    datasets = get_bigquery_dataset(bigquery, project_id, common_job_parameters)
    bigquery_datasets = transform_bigquery_dataset(bigquery, datasets, project_id)
    load_bigquery_datasets(neo4j_session, bigquery_datasets, project_id, gcp_update_tag)
    label.sync_labels(neo4j_session, bigquery_datasets, gcp_update_tag, common_job_parameters, 'bigquerydataset', 'GCPBigqueryDataset')

    # BIGQUERY TABLES
    for dataset in bigquery_datasets:
        accesses = get_dataset_access_info(bigquery, dataset['id'], project_id)
        accesses_list = transform_dataset_accesses(accesses, dataset['id'], project_id)
        attach_dataset_to_accesses(neo4j_session, dataset['id'], accesses_list, gcp_update_tag)
        tables = get_bigquery_tables(bigquery, dataset, project_id, common_job_parameters)
        bigquery_tables = transform_bigquery_tables(bigquery, dataset, tables, project_id)
        load_bigquery_tables(neo4j_session, bigquery_tables, project_id, gcp_update_tag)
        label.sync_labels(neo4j_session, bigquery_tables, gcp_update_tag, common_job_parameters, 'bigquerytable', 'GCPBigqueryTable')

    cleanup_gcp_bigquery(neo4j_session, common_job_parameters)

    toc = time.perf_counter()
    logger.info(f"Time to process GCP Big query: {toc - tic:0.4f} seconds")
