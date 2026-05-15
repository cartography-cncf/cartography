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
def get_spanner_instances(spanner: Resource, project_id: str, regions: list, common_job_parameters) -> List[Dict]:
    instances = []
    try:
        req = spanner.projects().instances().list(parent=f"projects/{project_id}")
        while req is not None:
            res = req.execute()
            if res.get('instances'):
                instances.extend(res.get('instances', []))
            req = spanner.projects().instances().list_next(previous_request=req, previous_response=res)
        return instances
    except HttpError as e:
        err = json.loads(e.content.decode('utf-8'))['error']
        if err.get('status', '') == 'PERMISSION_DENIED' or err.get('message', '') == 'Forbidden':
            logger.warning(
                (
                    'Could not retrieve spanner instances on project %s due to permissions issues. Code: %s, Message: %s'
                ), project_id, err['code'], err['message'],
            )
            return []
        else:
            raise


@timeit
def transform_instances(instances: List[Dict], project_id: str) -> List[Dict]:
    transformed_instances = []
    for instance in instances:
        instance['project_id'] = project_id
        instance['region'] = 'global'
        instance['id'] = instance['name']
        instance['instance_name'] = instance['name'].split('/')[-1]
        instance['consolelink'] = ''  # TODO
        transformed_instances.append(instance)
    return transformed_instances


@timeit
def load_spanner_instances(session: neo4j.Session, data_list: List[Dict], project_id: str, update_tag: int) -> None:
    session.execute_write(load_spanner_instances_tx, data_list, project_id, update_tag)


@timeit
def load_spanner_instances_tx(tx: neo4j.Transaction, data: List[Dict], project_id: str, gcp_update_tag: int) -> None:
    query = """
    UNWIND $Records as record
    MERGE (instance:GCPSpannerInstance{id:record.id})
    ON CREATE SET
        instance.firstseen = timestamp()
    SET
        instance.lastupdated = $gcp_update_tag,
        instance.region = record.region,
        instance.name = record.instance_name,
        instance.config = record.config,
        instance.create_time = record.createTime,
        instance.display_name = record.displayName,
        instance.instance_type = record.instanceType,
        instance.node_count = record.nodeCount,
        instance.processing_units = record.processingUnits,
        instance.state = record.state,
        instance.update_time = record.updateTime,
        instance.consolelink = record.consolelink
    WITH instance
    MATCH (owner:GCPProject{id: $ProjectId})
    MERGE (owner)-[r:RESOURCE]->(instance)
    ON CREATE SET
        r.firstseen = timestamp()
    SET r.lastupdated = $gcp_update_tag
    """
    tx.run(query=query, Records=data, ProjectId=project_id, gcp_update_tag=gcp_update_tag)


@timeit
def cleanup_spanner_instances(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('gcp_spanner_instances_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def get_spanner_instance_configs(spanner: Resource, project_id: str, regions: list, common_job_parameters) -> List[Dict]:
    instance_configs = []
    try:
        req = spanner.projects().instanceConfigs().list(parent=f"projects/{project_id}")
        while req is not None:
            res = req.execute()
            if res.get('instanceConfigs'):
                instance_configs.extend(res.get('instanceConfigs', []))
            req = spanner.projects().instanceConfigs().list_next(previous_request=req, previous_response=res)
        return instance_configs
    except HttpError as e:
        err = json.loads(e.content.decode('utf-8'))['error']
        if err.get('status', '') == 'PERMISSION_DENIED' or err.get('message', '') == 'Forbidden':
            logger.warning(
                (
                    'Could not retrieve spanner instanceConfigs on project %s due to permissions issues. Code: %s, Message: %s'
                ), project_id, err['code'], err['message'],
            )
            return []
        else:
            raise


@timeit
def transform_instance_configs(instance_configs: List[Dict], project_id: str) -> List[Dict]:
    transformed_instance_configs = []
    for instance_config in instance_configs:
        instance_config['project_id'] = project_id
        instance_config['region'] = 'global'
        instance_config['id'] = instance_config['name']
        instance_config['instance_config_name'] = instance_config['name'].split('/')[-1]
        instance_config['consolelink'] = ''  # TODO
        transformed_instance_configs.append(instance_config)
    return transformed_instance_configs


@timeit
def load_spanner_instance_configs(session: neo4j.Session, data_list: List[Dict], project_id: str, update_tag: int) -> None:
    session.execute_write(load_spanner_instance_configs_tx, data_list, project_id, update_tag)


@timeit
def load_spanner_instance_configs_tx(tx: neo4j.Transaction, data: List[Dict], project_id: str, gcp_update_tag: int) -> None:
    query = """
    UNWIND $Records as record
    MERGE (instance_config:GCPSpannerInstanceConfig{id: record.id})
    ON CREATE SET
        instance_config.firstseen = timestamp()
    SET
        instance_config.lastupdated = $gcp_update_tag,
        instance_config.region = record.region,
        instance_config.name = record.instance_config_name,
        instance_config.base_config = record.baseConfig,
        instance_config.config_type = record.configType,
        instance_config.display_name = record.displayName,
        instance_config.free_instance_availability = record.freeInstanceAvailability,
        instance_config.reconciling = record.reconciling,
        instance_config.state = record.state
    WITH instance_config
    MATCH (instance:GCPSpannerInstance{config:instance_config.id})
    MERGE (instance)-[rt:HAS]->(instance_config)
    ON CREATE SET
        rt.firstseen = timestamp()
    SET rt.lastupdated = $gcp_update_tag
    """
    tx.run(query=query, Records=data, ProjectId=project_id, gcp_update_tag=gcp_update_tag)


@timeit
def cleanup_spanner_instance_configs(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('gcp_spanner_instance_configs_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def transform_spanner_instance_configs_replicas(instance_configs: List[Dict], project_id: str, regions: list, common_job_parameters):
    all_replicas = []
    for instance_config in instance_configs:
        replicas = instance_config.get('replicas', [])
        for replica in replicas:
            replica['config'] = instance_config.get('name')
            replica['id'] = f"{instance_config.get('name')}/replicas/{replica.get('location')}"
        all_replicas.extend(replicas)
    return all_replicas


@timeit
def load_spanner_instance_configs_replicas(session: neo4j.Session, data_list: List[Dict], project_id: str, update_tag: int) -> None:
    session.execute_write(load_spanner_instance_configs_replicas_tx, data_list, project_id, update_tag)


@timeit
def load_spanner_instance_configs_replicas_tx(tx: neo4j.Transaction, data: List[Dict], project_id: str, gcp_update_tag: int) -> None:
    query = """
    UNWIND $Records as record
    MERGE (replica:GCPSpannerInstanceConfigReplica{id: record.id})
    ON CREATE SET
        replica.firstseen = timestamp()
    SET
        replica.lastupdated = $gcp_update_tag,
        replica.default_leader_location = record.defaultLeaderLocation,
        replica.location = record.location,
        replica.type = record.type
    WITH replica, record
    MATCH (instance_config:GCPSpannerInstanceConfig{id: record.config})
    MERGE (instance_config)-[rt:HAS]->(replica)
    ON CREATE SET
        rt.firstseen = timestamp()
    SET rt.lastupdated = $gcp_update_tag
    """
    tx.run(query=query, Records=data, ProjectId=project_id, gcp_update_tag=gcp_update_tag)


@timeit
def cleanup_spanner_instance_configs_replicas(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('gcp_spanner_instance_configs_replicas_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def get_spanner_instances_databases(spanner: Resource, instance: Dict, project_id: str, regions: list, common_job_parameters) -> List[Dict]:
    databases = []
    try:
        req = spanner.projects().instances().databases().list(parent=instance['name'])
        while req is not None:
            res = req.execute()
            if res.get('databases'):
                databases.extend(res.get('databases', []))
            req = spanner.projects().instances().databases().list_next(previous_request=req, previous_response=res)
        return databases
    except HttpError as e:
        err = json.loads(e.content.decode('utf-8'))['error']
        if err.get('status', '') == 'PERMISSION_DENIED' or err.get('message', '') == 'Forbidden':
            logger.warning(
                (
                    'Could not retrieve spanner instance databases on project %s due to permissions issues. Code: %s, Message: %s'
                ), project_id, err['code'], err['message'],
            )
            return []
        else:
            raise


@timeit
def transform_instances_databases(databases: List[Dict], project_id: str) -> List[Dict]:
    transformed_databases = []
    for database in databases:
        database['project_id'] = project_id
        database['region'] = 'global'
        database['id'] = database['name']
        database['database_name'] = database['name'].split('/')[-1]
        database['instance_id'] = "/".join(database['name'].split('/')[:-2])
        database['consolelink'] = ''  # TODO
        transformed_databases.append(database)
    return transformed_databases


@timeit
def load_spanner_instances_databases(session: neo4j.Session, data_list: List[Dict], project_id: str, update_tag: int) -> None:
    session.execute_write(load_spanner_instances_databases_tx, data_list, project_id, update_tag)


@timeit
def load_spanner_instances_databases_tx(tx: neo4j.Transaction, data: List[Dict], project_id: str, gcp_update_tag: int) -> None:
    query = """
    UNWIND $Records as record
    MERGE (database:GCPSpannerInstanceDatabase{id: record.id})
    ON CREATE SET
        database.firstseen = timestamp()
    SET
        database.lastupdated = $gcp_update_tag,
        database.region = record.region,
        database.name = record.database_name,
        database.create_time = record.createTime,
        database.database_dialect = record.databaseDialect,
        database.default_leader = record.defaultLeader,
        database.earliest_version_time = record.earliestVersionTime,
        database.kms_key_name = record.encryptionConfig.kmsKeyName,
        database.backup = record.restoreInfo.backupInfo.backup,
        database.source_type = record.restoreInfo.sourceType,
        database.state = record.state,
        database.version_retention_period = record.versionRetentionPeriod,
        database.consolelink = record.consolelink
    WITH database, record
    MATCH (instance:GCPSpannerInstance{id: record.instance_id})
    MERGE (instance)-[r:HAS_DATABASE]->(database)
    ON CREATE SET
        r.firstseen = timestamp()
    SET r.lastupdated = $gcp_update_tag
    WITH database
    MATCH (backup:GCPSpannerInstanceBackup{id: database.backup})
    MERGE (database)-[rt:HAS_BACKUP]->(backup)
    ON CREATE SET
        rt.firstseen = timestamp()
    SET rt.lastupdated = $gcp_update_tag
    """
    tx.run(query=query, Records=data, ProjectId=project_id, gcp_update_tag=gcp_update_tag)


@timeit
def cleanup_spanner_instance_databases(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('gcp_spanner_instance_databases_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def get_spanner_instances_backups(spanner: Resource, instance: Dict, project_id: str, regions: list, common_job_parameters) -> List[Dict]:
    backups = []
    try:
        req = spanner.projects().instances().backups().list(parent=instance['name'])
        while req is not None:
            res = req.execute()
            if res.get('backups'):
                backups.extend(res.get('backups', []))
            req = spanner.projects().instances().backups().list_next(previous_request=req, previous_response=res)
        return backups
    except HttpError as e:
        err = json.loads(e.content.decode('utf-8'))['error']
        if err.get('status', '') == 'PERMISSION_DENIED' or err.get('message', '') == 'Forbidden':
            logger.warning(
                (
                    'Could not retrieve spanner instance backups on project %s due to permissions issues. Code: %s, Message: %s'
                ), project_id, err['code'], err['message'],
            )
            return []
        else:
            raise


@timeit
def transform_instances_backups(backups: List[Dict], project_id: str) -> List[Dict]:
    transformed_backups = []
    for backup in backups:
        backup['project_id'] = project_id
        backup['region'] = 'global'
        backup['backup_name'] = backup['name'].split('/')[-1]
        backup['id'] = backup['name']
        backup['instance_id'] = "/".join(backup['name'].split('/')[:-2])
        backup['consolelink'] = ''  # TODO
        transformed_backups.append(backup)
    return transformed_backups


@timeit
def load_spanner_instances_backups(session: neo4j.Session, data_list: List[Dict], project_id: str, update_tag: int) -> None:
    session.execute_write(load_spanner_instances_backups_tx, data_list, project_id, update_tag)


@timeit
def load_spanner_instances_backups_tx(tx: neo4j.Transaction, data: List[Dict], project_id: str, gcp_update_tag: int) -> None:
    query = """
    UNWIND $Records as record
    MERGE (backup:GCPSpannerInstanceBackup{id: record.id})
    ON CREATE SET
        backup.firstseen = timestamp()
    SET
        backup.lastupdated = $gcp_update_tag,
        backup.region = record.region,
        backup.name = record.backup_name,
        backup.create_time = record.createTime,
        backup.database = record.database,
        backup.database_dialect = record.databaseDialect,
        backup.encryption_type = record.encryptionInfo.encryptionType,
        backup.kms_key_version = record.encryptionInfo.kmsKeyVersion,
        backup.expire_time = record.expireTime,
        backup.max_expire_time = record.maxExpireTime,
        backup.referencing_backups = record.referencingBackups,
        backup.referencing_databases = record.referencingDatabases,
        backup.size_bytes = record.sizeBytes,
        backup.state = record.state,
        backup.version_time = record.versionTime,
        backup.consolelink = record.consolelink
    WITH backup, record
    MATCH (instance:GCPSpannerInstance{id: record.instance_id})
    MERGE (instance)-[r:HAS_BACKUP]->(backup)
    ON CREATE SET
        r.firstseen = timestamp()
    SET r.lastupdated = $gcp_update_tag
    """
    tx.run(query=query, Records=data, ProjectId=project_id, gcp_update_tag=gcp_update_tag)


@timeit
def cleanup_spanner_instance_backups(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('gcp_spanner_instance_backups_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync(
    neo4j_session: neo4j.Session, spanner: Resource, project_id: str, gcp_update_tag: int,
    common_job_parameters: Dict, regions: List,
) -> None:
    tic = time.perf_counter()
    logger.info("Syncing spanner for project '%s', at %s.", project_id, tic)

    instances = get_spanner_instances(spanner, project_id, regions, common_job_parameters)
    transformed_instances = transform_instances(instances, project_id)
    load_spanner_instances(neo4j_session, transformed_instances, project_id, gcp_update_tag)
    label.sync_labels(
        neo4j_session, transformed_instances, gcp_update_tag, common_job_parameters,
        'spanner_instances', 'GCPSpannerInstance',
    )

    instance_configs = get_spanner_instance_configs(spanner, project_id, regions, common_job_parameters)
    transformed_instance_configs = transform_instance_configs(instance_configs, project_id)
    load_spanner_instance_configs(neo4j_session, transformed_instance_configs, project_id, gcp_update_tag)
    label.sync_labels(
        neo4j_session, transformed_instance_configs, gcp_update_tag, common_job_parameters,
        'spanner_instance_configs', 'GCPSpannerInstanceConfig',
    )

    replicas = transform_spanner_instance_configs_replicas(instance_configs, project_id, regions, common_job_parameters)
    load_spanner_instance_configs_replicas(neo4j_session, replicas, project_id, gcp_update_tag)

    for instance in instances:
        backups = get_spanner_instances_backups(spanner, instance, project_id, regions, common_job_parameters)
        transformed_backups = transform_instances_backups(backups, project_id)
        load_spanner_instances_backups(neo4j_session, transformed_backups, project_id, gcp_update_tag)

        databases = get_spanner_instances_databases(spanner, instance, project_id, regions, common_job_parameters)
        transformed_databases = transform_instances_databases(databases, project_id)
        load_spanner_instances_databases(neo4j_session, transformed_databases, project_id, gcp_update_tag)

    cleanup_spanner_instance_configs_replicas(neo4j_session, common_job_parameters)
    cleanup_spanner_instance_configs(neo4j_session, common_job_parameters)
    cleanup_spanner_instance_backups(neo4j_session, common_job_parameters)
    cleanup_spanner_instance_databases(neo4j_session, common_job_parameters)
    cleanup_spanner_instances(neo4j_session, common_job_parameters)
    toc = time.perf_counter()
    logger.info(f"Time to process Spanner: {toc - tic:0.4f} seconds")
