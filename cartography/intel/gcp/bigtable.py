import json
import logging
from typing import Dict
from typing import List

import neo4j
from googleapiclient.discovery import HttpError
from googleapiclient.discovery import Resource

from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_bigtable_instances(bigtable: Resource, project_id: str) -> List[Dict]:
    """
        Returns a list of bigtable instances for a given project.

        :type bigtable: Resource
        :param bigtable: The bigtable resource created by googleapiclient.discovery.build()

        :type project_id: str
        :param project_id: Current Google Project Id

        :rtype: list
        :return: List of Bigtable Instances
    """
    try:
        bigtable_instances = []
        request = bigtable.projects().instances().list(parent=f"projects/{project_id}")
        while request is not None:
            response = request.execute()
            if response.get('instances', []):
                for instance in response['instances']:
                    instance['id'] = instance['name']
                    bigtable_instances.append(instance)
            request = bigtable.projects().instances().list_next(previous_request=request, previous_response=response)
        return bigtable_instances
    except HttpError as e:
        err = json.loads(e.content.decode('utf-8'))['error']
        if err.get('status', '') == 'PERMISSION_DENIED' or err.get('message', '') == 'Forbidden':
            logger.warning(
                (
                    "Could not retrieve Bigtable Instances on project %s due to permissions issues.\
                         Code: %s, Message: %s"
                ), project_id, err['code'], err['message'],
            )
            return []
        else:
            raise


@timeit
def get_bigtable_clusters(bigtable: Resource, bigtable_instances: List[Dict], project_id: str) -> List[Dict]:
    """
        Returns a list of bigtable clusters for a given project.

        :type bigtable: Resource
        :param bigtable: The bigtable resource created by googleapiclient.discovery.build()

        :type bigtable_instances: List
        :param bigtable_instances: A list of bigtable instances

        :type project_id: str
        :param project_id: Current Google Project Id

        :rtype: list
        :return: List of Bigtable Clusters
    """
    bigtable_clusters = []
    for instance in bigtable_instances:
        try:
            request = bigtable.projects().instances().clusters().list(
                parent=instance['name'],
            )
            while request is not None:
                response = request.execute()
                if response.get('clusters', []):
                    for cluster in response['clusters']:
                        cluster['instance_id'] = instance['id']
                        cluster['instance_name'] = instance.get('name')
                        cluster['id'] = cluster['name']
                        bigtable_clusters.append(cluster)
                request = bigtable.projects().instances().clusters().list_next(
                    previous_request=request, previous_response=response,
                )
        except HttpError as e:
            err = json.loads(e.content.decode('utf-8'))['error']
            if err.get('status', '') == 'PERMISSION_DENIED' or err.get('message', '') == 'Forbidden':
                logger.warning(
                    (
                        "Could not retrieve Bigtable Instance Clusters on project %s due to permissions issues.\
                            Code: %s, Message: %s"
                    ), project_id, err['code'], err['message'],
                )
                return []
            else:
                raise
    return bigtable_clusters


@timeit
def get_bigtable_cluster_backups(bigtable: Resource, bigtable_clusters: List[Dict], project_id: str) -> List[Dict]:
    """
        Returns a list of bigtable cluster backups for a given project.

        :type bigtable: Resource
        :param bigtable: The bigtable resource created by googleapiclient.discovery.build()

        :type bigtable_clusters: list
        :param bigtable_clusters: List of bigtable clusters

        :type project_id: str
        :param project_id: Current Google Project Id

        :rtype: list
        :return: List of Bigtable Cluster Backups
    """
    cluster_backups = []
    for cluster in bigtable_clusters:
        try:
            request = bigtable.projects().instances().clusters().backup().list(
                parent=cluster.get('name', None),
            )
            while request is not None:
                response = request.execute()
                if response.get('backups', []):
                    for backup in response['backups']:
                        backup['cluster_id'] = cluster['id']
                        backup['id'] = backup['name']
                        cluster_backups.append(backup)
                request = bigtable.projects().instances().clusters().backup().list_next(
                    previous_request=request, previous_response=response,
                )
        except HttpError as e:
            err = json.loads(e.content.decode('utf-8'))['error']
            if err.get('status', '') == 'PERMISSION_DENIED' or err.get('message', '') == 'Forbidden':
                logger.warning(
                    (
                        "Could not retrieve Bigtable Instance Clusters Backups on project %s due to permissions issues.\
                             Code: %s, Message: %s"
                    ), project_id, err['code'], err['message'],
                )
                return []
            else:
                raise
    return cluster_backups


@timeit
def get_get_bigtable_tables(bigtable: Resource, bigtable_instances: List[Dict], project_id: str) -> List[Dict]:
    """
        Returns a list of bigtable tables for a given project.

        :type bigtable: Resource
        :param bigtable: The bigtable resource created by googleapiclient.discovery.build()

        :type bigtable_instances: List
        :param bigtable_instances: List of bigtable instances

        :type project_id: str
        :param project_id: Current Google Project Id

        :rtype: list
        :return: List of Bigtable Tables
    """
    bigtable_tables = []
    for instance in bigtable_instances:
        try:
            request = bigtable.projects().instances().tables().list(
                parent=instance.get('name', None),
            )
            while request is not None:
                response = request.execute()
                if response.get('tables', []):
                    for table in response['tables']:
                        table['instance_id'] = instance['id']
                        table['id'] = table['name']
                        bigtable_tables.append(table)
                request = bigtable.projects().instances().tables().list_next(
                    previous_request=request, previous_response=response,
                )
        except HttpError as e:
            err = json.loads(e.content.decode('utf-8'))['error']
            if err.get('status', '') == 'PERMISSION_DENIED' or err.get('message', '') == 'Forbidden':
                logger.warning(
                    (
                        "Could not retrieve Bigtable Instance Tables on project %s due to permissions issues.\
                             Code: %s, Message: %s"
                    ), project_id, err['code'], err['message'],
                )
                return []
            else:
                raise
    return bigtable_tables


@timeit
def load_bigtable_instances(session: neo4j.Session, data_list: List[Dict], project_id: str, update_tag: int) -> None:
    session.write_transaction(_load_bigtable_instances_tx, data_list, project_id, update_tag)


@timeit
def _load_bigtable_instances_tx(
    tx: neo4j.Transaction, bigtable_instances: List[Dict],
    project_id: str, gcp_update_tag: int,
) -> None:
    """
        :type neo4j_transaction: Neo4j transaction object
        :param neo4j transaction: The Neo4j transaction object

        :type instances_resp: List
        :param instances_resp: A list of Bigtable Instances

        :type project_id: str
        :param project_id: Current Google Project Id

        :type gcp_update_tag: timestamp
        :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with
    """
    ingest_bigtable_instances = """
    UNWIND {bigtable_instances} as instance
    MERGE (i:GCPBigtableInstance{id:instance.id})
    ON CREATE SET
        i.firstseen = timestamp()
    SET
        i.name = instance.name,
        i.displayName = instance.displayName,
        i.state = instance.state,
        i.type = instance.type,
        i.createTime = instance.createTime,
        i.lastupdated = {gcp_update_tag}
    WITH instance, i
    MATCH (owner:GCPProject{id:{ProjectId}})
    MERGE (owner)-[r:RESOURCE]->(i)
    ON CREATE SET
        r.firstseen = timestamp(),
        r.lastupdated = {gcp_update_tag}
    """
    tx.run(
        ingest_bigtable_instances,
        bigtable_instances=bigtable_instances,
        ProjectId=project_id,
        gcp_update_tag=gcp_update_tag,
    )


@timeit
def load_bigtable_clusters(session: neo4j.Session, data_list: List[Dict], project_id: str, update_tag: int) -> None:
    session.write_transaction(_load_bigtable_clusters_tx, data_list, project_id, update_tag)


@timeit
def _load_bigtable_clusters_tx(
    tx: neo4j.Transaction, bigtable_clusters: List[Dict],
    project_id: str, gcp_update_tag: int,
) -> None:
    """
        :type neo4j_transaction: Neo4j transaction object
        :param neo4j transaction: The Neo4j transaction object

        :type clusters_resp: List
        :param clusters_resp: A list of Bigtable Instance Clusters

        :type project_id: str
        :param project_id: Current Google Project Id

        :type gcp_update_tag: timestamp
        :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with
    """
    ingest_bigtable_clusters = """
    UNWIND {bigtable_clusters} as cluster
    MERGE (c:GCPBigtableCluster{id:cluster.id})
    ON CREATE SET
        c.firstseen = timestamp()
    SET
        c.name = cluster.name,
        c.location = cluster.name,
        c.state = cluster.state,
        c.serveNodes = cluster.serveNodes,
        c.defaultStorageType = cluster.defaultStorageType,
        c.lastupdated = {gcp_update_tag}
    WITH c,cluster
    MATCH (i:GCPBigtableInstance{id:cluster.instance_id})
    MERGE (i)-[r:HAS_CLUSTER]->(c)
    ON CREATE SET
        r.firstseen = timestamp(),
        r.lastupdated = {gcp_update_tag}
    """
    tx.run(
        ingest_bigtable_clusters,
        bigtable_clusters=bigtable_clusters,
        ProjectId=project_id,
        gcp_update_tag=gcp_update_tag,
    )


@timeit
def load_bigtable_cluster_backups(
    session: neo4j.Session, data_list: List[Dict],
    project_id: str, update_tag: int,
) -> None:
    session.write_transaction(_load_bigtable_cluster_backups_tx, data_list, project_id, update_tag)


@timeit
def _load_bigtable_cluster_backups_tx(
    tx: neo4j.Transaction, bigtable_cluster_backups: List[Dict],
    project_id: str, gcp_update_tag: int,
) -> None:
    """
        :type neo4j_transaction: Neo4j transaction object
        :param neo4j transaction: The Neo4j transaction object

        :type cluster_backup_resp: List
        :param cluster_backup_resp: A list of Bigtable Instance Cluster Backups

        :type project_id: str
        :param project_id: Current Google Project Id

        :type gcp_update_tag: timestamp
        :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with
    """
    ingest_bigtable_cluster_backups = """
    UNWIND {bigtable_cluster_backups} as backup
    MERGE (b:GCPBigtableClusterBackup{id:backup.id})
    ON CREATE SET
        b.firstseen = timestamp()
    SET
        b.name = backup.name,
        b.sourceTable = backup.sourceTable,
        b.expireTime = backup.expireTime,
        b.startTime = backup.startTime,
        b.endTime = backup.endTime,
        b.sizeBytes = backup.sizeBytes,
        b.state = backup.state,
        b.lastupdated = {gcp_update_tag}
    WITH b,backup
    MATCH (c:GCPBigtableCluster{id:backup.cluster_id})
    MERGE (c)-[r:HAS_BACKUP]->(b)
    ON CREATE SET
        r.firstseen = timestamp(),
        r.lastupdated = {gcp_update_tag}
    """
    tx.run(
        ingest_bigtable_cluster_backups,
        bigtable_cluster_backups=bigtable_cluster_backups,
        ProjectId=project_id,
        gcp_update_tag=gcp_update_tag,
    )


@timeit
def load_bigtable_tables(session: neo4j.Session, data_list: List[Dict], project_id: str, update_tag: int) -> None:
    session.write_transaction(_load_bigtable_tables_tx, data_list, project_id, update_tag)


@timeit
def _load_bigtable_tables_tx(
    tx: neo4j.Transaction, bigtable_tables: List[Dict],
    project_id: str, gcp_update_tag: int,
) -> None:
    """
        :type neo4j_transaction: Neo4j transaction object
        :param neo4j transaction: The Neo4j transaction object

        :type bigtable_table_resp: List
        :param bigtable_table_resp: A list of Bigtable Tables

        :type project_id: str
        :param project_id: Current Google Project Id

        :type gcp_update_tag: timestamp
        :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with
    """
    ingest_bigtable_tables = """
    UNWIND {bigtable_tables} as table
    MERGE (t:GCPBigtableTable{id:table.id})
    ON CREATE SET
        t.firstseen = timestamp()
    SET
        t.name = table.name,
        t.replicationState = table.clusterState.replicationState,
        t.granularity = table.granularity,
        t.sourceType = table.restoreInfo.sourceType,
        t.lastupdated = {gcp_update_tag}
    WITH table, t
    MATCH (i:GCPBigtableInstance{id:table.instance_id})
    MERGE (i)-[r:HAS_TABLE]->(t)
    ON CREATE SET
        r.firstseen = timestamp(),
        r.lastupdated = {gcp_update_tag}
    """
    tx.run(
        ingest_bigtable_tables,
        bigtable_tables=bigtable_tables,
        ProjectId=project_id,
        gcp_update_tag=gcp_update_tag,
    )


@timeit
def cleanup_bigtable(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    """
        Delete out-of-date GCP Bigtable Instances,Clusters,Cluster Backups and Tables and relationships

        :type neo4j_session: The Neo4j session object
        :param neo4j_session: The Neo4j session

        :type common_job_parameters: dict
        :param common_job_parameters: Dictionary of other job parameters to pass to Neo4j

        :rtype: NoneType
        :return: Nothing
    """
    run_cleanup_job('gcp_bigtable_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync(
    neo4j_session: neo4j.Session, bigtable: Resource, project_id: str, gcp_update_tag: int,
    common_job_parameters: Dict,
) -> None:
    """
        Get GCP Cloud Bigtable Entities using the Cloud Bigtable resource object,
        ingest to Neo4j, and clean up old data.

        :type neo4j_session: The Neo4j session object
        :param neo4j_session: The Neo4j session

        :type bigtable: The GCP Bigtable resource object created by googleapiclient.discovery.build()
        :param sql: The GCP Bigtable resource object

        :type project_id: str
        :param project_id: The project ID of the corresponding project

        :type gcp_update_tag: timestamp
        :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with

        :type common_job_parameters: dict
        :param common_job_parameters: Dictionary of other job parameters to pass to Neo4j

        :rtype: NoneType
        :return: Nothing
    """
    logger.info("Syncing GCP Cloud Bigtable for project %s.", project_id)
    # BIGTABLE INSTANCES
    bigtable_instances = get_bigtable_instances(bigtable, project_id)
    load_bigtable_instances(neo4j_session, bigtable_instances, project_id, gcp_update_tag)
    # BIGTABLE CLUSTERS
    bigtable_clusters = get_bigtable_clusters(bigtable, bigtable_instances, project_id)
    load_bigtable_clusters(neo4j_session, bigtable_clusters, project_id, gcp_update_tag)
    # BIGTABLE CLUSTER BACKUPS
    cluster_backups = get_bigtable_cluster_backups(bigtable, bigtable_clusters, project_id)
    load_bigtable_cluster_backups(neo4j_session, cluster_backups, project_id, gcp_update_tag)
    # BIGTABLE TABLES
    bigtable_tables = get_get_bigtable_tables(bigtable, bigtable_instances, project_id)
    load_bigtable_tables(neo4j_session, bigtable_tables, project_id, gcp_update_tag)
    cleanup_bigtable(neo4j_session, common_job_parameters)
