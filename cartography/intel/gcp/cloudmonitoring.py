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
def get_monitoring_alertpolicies(monitoring: Resource, project_id: str) -> List[Dict]:
    policies = []
    try:
        req = monitoring.projects().alertPolicies().list(name=f"projects/{project_id}")
        while req is not None:
            res = req.execute()
            if res.get('alertPolicies'):
                for policy in res['alertPolicies']:
                    policy['region'] = 'global'
                    policy['id'] = policy['name']
                    policy['policy_name'] = policy.get('name').split('/')[-1]
                    policy['labels'] = policy.get('userLabels', {})
                    policy['consolelink'] = gcp_console_link.get_console_link(
                        project_id=project_id,
                        alert_policy_name=policy['name'], resource_name='cloud_monitoring_alert_policy',
                    )
                    policies.append(policy)
            req = monitoring.projects().alertPolicies().list_next(previous_request=req, previous_response=res)

        return policies
    except HttpError as e:
        err = json.loads(e.content.decode('utf-8'))['error']
        if err.get('status', '') == 'PERMISSION_DENIED' or err.get('message', '') == 'Forbidden':
            logger.warning(
                (
                    "Could not retrieve monitoring alertpolicies on project %s due to permissions issues. Code: %s, Message: %s"
                ), project_id, err['code'], err['message'],
            )
            return []
        else:
            raise


@timeit
def load_monitoring_alertpolicies(session: neo4j.Session, data_list: List[Dict], project_id: str, update_tag: int) -> None:
    session.execute_write(load_monitoring_alertpolicies_tx, data_list, project_id, update_tag)


@timeit
def load_monitoring_alertpolicies_tx(
    tx: neo4j.Transaction, data: List[Dict],
    project_id: str, gcp_update_tag: int,
) -> None:

    query = """
    UNWIND $Records as record
    MERGE (policy:GCPMonitoringAlertPolicy{id:record.id})
    ON CREATE SET
        policy.firstseen = timestamp()
    SET
        policy.lastupdated = $gcp_update_tag,
        policy.region = record.region,
        policy.name = record.policy_name,
        policy.display_name = record.displayName,
        policy.consolelink = record.consolelink,
        policy.enabled = record.enabled
    WITH policy
    MATCH (owner:GCPProject{id: $ProjectId})
    MERGE (owner)-[r:RESOURCE]->(policy)
    ON CREATE SET
        r.firstseen = timestamp()
    SET r.lastupdated = $gcp_update_tag
    """
    tx.run(
        query,
        Records=data,
        ProjectId=project_id,
        gcp_update_tag=gcp_update_tag,
    )


@timeit
def cleanup_monitoring_alertpolicies(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('gcp_monitoring_alertpolicies_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync_monitoring_alertpolicies(
    neo4j_session: neo4j.Session, monitoring: Resource, project_id: str,
    gcp_update_tag: int, common_job_parameters: Dict,
) -> None:

    policies = get_monitoring_alertpolicies(monitoring, project_id)

    load_monitoring_alertpolicies(neo4j_session, policies, project_id, gcp_update_tag)
    cleanup_monitoring_alertpolicies(neo4j_session, common_job_parameters)
    label.sync_labels(
        neo4j_session, policies, gcp_update_tag,
        common_job_parameters, 'monitoring_alertpolicies', 'GCPMonitoringAlertPolicy',
    )


@timeit
def get_monitoring_metric_descriptors(monitoring: Resource, project_id: str) -> List[Dict]:
    metric_descriptors = []
    try:
        req = monitoring.projects().metricDescriptors().list(name=f"projects/{project_id}")
        while req is not None:
            res = req.execute()
            if res.get('metricDescriptors'):
                metric_descriptors.extend(res.get('metricDescriptors', []))
            req = monitoring.projects().metricDescriptors().list_next(previous_request=req, previous_response=res)

        return metric_descriptors
    except HttpError as e:
        err = json.loads(e.content.decode('utf-8'))['error']
        if err.get('status', '') == 'PERMISSION_DENIED' or err.get('message', '') == 'Forbidden':
            logger.warning(
                (
                    "Could not retrieve monitoring metric descriptors on project %s due to permissions issues. Code: %s, Message: %s"
                ), project_id, err['code'], err['message'],
            )
            return []
        else:
            raise


@timeit
def transform_metric_descriptors(metric_descriptors: List[Dict], project_id: str) -> List[Dict]:
    metric_descriptors = []
    for metric in metric_descriptors:
        metric['region'] = 'global'
        metric['id'] = f"projects/{project_id}/metricDescriptors/{metric['name']}"
        metric['consolelink'] = gcp_console_link.get_console_link(project_id=project_id, resource_name='cloud_logging_metric')
        metric_descriptors.append(metric)

    return metric_descriptors


@timeit
def load_monitoring_metric_descriptors(session: neo4j.Session, data_list: List[Dict], project_id: str, update_tag: int) -> None:
    session.execute_write(load_monitoring_metric_descriptors_tx, data_list, project_id, update_tag)


@timeit
def load_monitoring_metric_descriptors_tx(
    tx: neo4j.Transaction, data: List[Dict],
    project_id: str, gcp_update_tag: int,
) -> None:

    query = """
    UNWIND $Records as record
    MERGE (descriptor:GCPMonitoringMetricDescriptor{id:record.id})
    ON CREATE SET
        descriptor.firstseen = timestamp()
    SET
        descriptor.lastupdated = $gcp_update_tag,
        descriptor.region = record.region,
        descriptor.name = record.name,
        descriptor.consolelink = record.consolelink,
        descriptor.display_name = record.displayName,
        descriptor.unit = record.unit,
        descriptor.description = record.description,
        descriptor.type = record.type
    WITH descriptor
    MATCH (owner:GCPProject{id: $ProjectId})
    MERGE (owner)-[r:RESOURCE]->(descriptor)
    ON CREATE SET
        r.firstseen = timestamp()
    SET r.lastupdated = $gcp_update_tag
    """
    tx.run(
        query,
        Records=data,
        ProjectId=project_id,
        gcp_update_tag=gcp_update_tag,
    )


@timeit
def cleanup_monitoring_metric_descriptors(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('gcp_monitoring_metric_descriptors_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync_monitoring_metric_descriptors(
    neo4j_session: neo4j.Session, monitoring: Resource, project_id: str,
    gcp_update_tag: int, common_job_parameters: Dict,
) -> None:

    metric_des = get_monitoring_metric_descriptors(monitoring, project_id)
    metric_descriptors = transform_metric_descriptors(metric_des, project_id)

    load_monitoring_metric_descriptors(neo4j_session, metric_descriptors, project_id, gcp_update_tag)
    cleanup_monitoring_metric_descriptors(neo4j_session, common_job_parameters)


@timeit
def get_monitoring_notification_channels(monitoring: Resource, project_id: str) -> List[Dict]:
    channels = []
    try:
        req = monitoring.projects().notificationChannels().list(name=f"projects/{project_id}")
        while req is not None:
            res = req.execute()
            if res.get('notificationChannels'):
                for channel in res['notificationChannels']:
                    channel['region'] = 'global'
                    channel['id'] = channel['name']
                    channel['channel_name'] = channel.get('name').split('/')[-1]
                    channel['consolelink'] = gcp_console_link.get_console_link(project_id=project_id, resource_name='cloud_monitoring_notification_channels')
                    channels.append(channel)
            req = monitoring.projects().notificationChannels().list_next(previous_request=req, previous_response=res)

        return channels
    except HttpError as e:
        err = json.loads(e.content.decode('utf-8'))['error']
        if err.get('status', '') == 'PERMISSION_DENIED' or err.get('message', '') == 'Forbidden':
            logger.warning(
                (
                    "Could not retrieve monitoring notification channels on project %s due to permissions issues. Code: %s, Message: %s"
                ), project_id, err['code'], err['message'],
            )
            return []
        else:
            raise


@timeit
def load_monitoring_notification_channels(session: neo4j.Session, data_list: List[Dict], project_id: str, update_tag: int) -> None:
    session.execute_write(load_monitoring_notification_channels_tx, data_list, project_id, update_tag)


@timeit
def load_monitoring_notification_channels_tx(
    tx: neo4j.Transaction, data: List[Dict],
    project_id: str, gcp_update_tag: int,
) -> None:

    query = """
    UNWIND $Records as record
    MERGE (channel:GCPMonitoringNotificationChannel{id:record.id})
    ON CREATE SET
        channel.firstseen = timestamp()
    SET
        channel.lastupdated = $gcp_update_tag,
        channel.region = record.region,
        channel.name = record.channel_name,
        channel.display_name = record.displayName,
        channel.enabled = record.enabled,
        channel.consolelink = record.consolelink,
        channel.description = record.description,
        channel.type = record.type
    WITH channel
    MATCH (owner:GCPProject{id: $ProjectId})
    MERGE (owner)-[r:RESOURCE]->(channel)
    ON CREATE SET
        r.firstseen = timestamp()
    SET r.lastupdated = $gcp_update_tag
    """
    tx.run(
        query,
        Records=data,
        ProjectId=project_id,
        gcp_update_tag=gcp_update_tag,
    )


@timeit
def cleanup_monitoring_notification_channels(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('gcp_monitoring_notification_channels_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync_monitoring_notification_channels(
    neo4j_session: neo4j.Session, monitoring: Resource, project_id: str,
    gcp_update_tag: int, common_job_parameters: Dict,
) -> None:

    channels = get_monitoring_notification_channels(monitoring, project_id)

    load_monitoring_notification_channels(neo4j_session, channels, project_id, gcp_update_tag)
    cleanup_monitoring_notification_channels(neo4j_session, common_job_parameters)
    label.sync_labels(
        neo4j_session, channels, gcp_update_tag,
        common_job_parameters, 'monitoring_notification_channels', 'GCPMonitoringNotificationChannel',
    )


@timeit
def get_monitoring_uptimecheckconfigs(monitoring: Resource, project_id: str) -> List[Dict]:
    configs = []
    try:
        req = monitoring.projects().uptimeCheckConfigs().list(parent=f"projects/{project_id}")
        while req is not None:
            res = req.execute()
            if res.get('notificationChannels'):
                for config in res['notificationChannels']:
                    config['region'] = 'global'
                    config['id'] = config['name']
                    config['config_name'] = config.get('name').split('/')[-1]
                    config['labels'] = config.get('userLabels', {})
                    config['consolelink'] = gcp_console_link.get_console_link(
                        project_id=project_id,
                        uptimecheck_config_name=config['name'], resource_name='cloud_monitoring_uptime_check_config',
                    )
                    configs.append(config)
            req = monitoring.projects().uptimeCheckConfigs().list_next(previous_request=req, previous_response=res)

        return configs
    except HttpError as e:
        err = json.loads(e.content.decode('utf-8'))['error']
        if err.get('status', '') == 'PERMISSION_DENIED' or err.get('message', '') == 'Forbidden':
            logger.warning(
                (
                    "Could not retrieve monitoring uptime check configs on project %s due to permissions issues. Code: %s, Message: %s"
                ), project_id, err['code'], err['message'],
            )
            return []
        else:
            raise


@timeit
def load_monitoring_uptimecheckconfigs(session: neo4j.Session, data_list: List[Dict], project_id: str, update_tag: int) -> None:
    session.execute_write(load_monitoring_uptimecheckconfigs_tx, data_list, project_id, update_tag)


@timeit
def load_monitoring_uptimecheckconfigs_tx(
    tx: neo4j.Transaction, data: List[Dict],
    project_id: str, gcp_update_tag: int,
) -> None:

    query = """
    UNWIND $Records as record
    MERGE (config:GCPMonitoringUptimeCheckConfig{id:record.id})
    ON CREATE SET
        config.firstseen = timestamp()
    SET
        config.lastupdated = $gcp_update_tag,
        config.region = record.region,
        config.name = record.config_name,
        config.display_name = record.displayName,
        config.is_internal = record.isInternal,
        config.timeout = record.timeout,
        config.consolelink = record.consolelink,
        config.period = record.period
    WITH config
    MATCH (owner:GCPProject{id: $ProjectId})
    MERGE (owner)-[r:RESOURCE]->(config)
    ON CREATE SET
        r.firstseen = timestamp()
    SET r.lastupdated = $gcp_update_tag
    """
    tx.run(
        query,
        Records=data,
        ProjectId=project_id,
        gcp_update_tag=gcp_update_tag,
    )


@timeit
def cleanup_monitoring_uptimecheckconfigs(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('gcp_monitoring_uptimecheckconfigs_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync_monitoring_uptimecheckconfigs(
    neo4j_session: neo4j.Session, monitoring: Resource, project_id: str,
    gcp_update_tag: int, common_job_parameters: Dict,
) -> None:

    configs = get_monitoring_uptimecheckconfigs(monitoring, project_id)

    load_monitoring_uptimecheckconfigs(neo4j_session, configs, project_id, gcp_update_tag)
    cleanup_monitoring_uptimecheckconfigs(neo4j_session, common_job_parameters)
    label.sync_labels(
        neo4j_session, configs, gcp_update_tag,
        common_job_parameters, 'monitoring_uptimecheckconfigs', 'GCPMonitoringUptimeCheckConfig',
    )


def sync(
    neo4j_session: neo4j.Session, monitoring: Resource, project_id: str, gcp_update_tag: int,
    common_job_parameters: dict, regions: list,
) -> None:

    tic = time.perf_counter()

    logger.info(f"Syncing monitoring for project {project_id}, at {tic}")

    sync_monitoring_alertpolicies(
        neo4j_session, monitoring, project_id,
        gcp_update_tag, common_job_parameters,
    )
    sync_monitoring_metric_descriptors(
        neo4j_session, monitoring, project_id,
        gcp_update_tag, common_job_parameters,
    )
    sync_monitoring_notification_channels(
        neo4j_session, monitoring, project_id,
        gcp_update_tag, common_job_parameters,
    )
    sync_monitoring_uptimecheckconfigs(
        neo4j_session, monitoring, project_id,
        gcp_update_tag, common_job_parameters,
    )

    toc = time.perf_counter()
    logger.info(f"Time to process monitoring: {toc - tic:0.4f} seconds")
