import logging
from typing import Dict
from typing import List

import neo4j
from azure.core.exceptions import ClientAuthenticationError
from azure.core.exceptions import HttpResponseError
from azure.core.exceptions import ResourceNotFoundError
from azure.mgmt.monitor import MonitorManagementClient
from cloudconsolelink.clouds.azure import AzureLinker

from .util.credentials import Credentials
from cartography.util import get_azure_resource_group_name
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)
azure_console_link = AzureLinker()


def load_monitor_log_profiles(session: neo4j.Session, subscription_id: str, data_list: List[Dict], update_tag: int) -> None:
    session.execute_write(_load_monitor_log_profiles_tx, subscription_id, data_list, update_tag)


@timeit
def get_monitoring_client(credentials: Credentials, subscription_id: str) -> MonitorManagementClient:
    client = MonitorManagementClient(credentials, subscription_id)
    return client


@timeit
def get_log_profiles_list(client: MonitorManagementClient, regions: List, common_job_parameters: Dict) -> List[Dict]:
    try:
        list_logs_profiles = list(map(lambda x: x.as_dict(), client.log_profiles.list()))
        return list_logs_profiles
    except ClientAuthenticationError as e:
        logger.warning(f"Client Authentication Error while  logs profiles - {e}")
        return []
    except ResourceNotFoundError as e:
        logger.warning(f" logs profiles not found error - {e}")
        return []
    except HttpResponseError as e:
        logger.warning(f"Error while  logs profiles - {e}")
        return []


@timeit
def transform_log_profiles(log_profiles: List[Dict], regions: List, common_job_parameters: str):
    log_profiles_data = []
    for log in log_profiles:
        log['resource_group'] = get_azure_resource_group_name(log.get('id'))
        log['consolelink'] = azure_console_link.get_console_link(
            id=log['id'], primary_ad_domain_name=common_job_parameters['Azure_Primary_AD_Domain_Name'],
        )
        log['location'] = log.get('location', '').replace(" ", "").lower()
        if regions is None:
            log_profiles_data.append(log)
        else:
            if log.get('location') in regions or log.get('location') == 'global':
                log_profiles_data.append(log)
    return log_profiles_data


@timeit
def _load_monitor_log_profiles_tx(
    tx: neo4j.Transaction, subscription_id: str, log_profiles_list: List[Dict], update_tag: int,
) -> None:

    query = """
    UNWIND $LOGS as l
    MERGE (log:AzureMonitorLogProfile{id: l.id})
    ON CREATE SET log.firstseen = timestamp(),
    log.type = l.type,
    log.name = l.name,
    log.consolelink = l.consolelink,
    log.resourcegroup = l.resource_group,
    log.location = l.location,
    log.region = l.location,
    log.service_bus_rule_id = l.service_bus_rule_id,
    log.storage_account_id = l.storage_account_id
    SET log.lastupdated = $update_tag,
    log.name = l.name,
    log.region = l.location
    WITH log
    MATCH (owner:AzureSubscription{id: $SUBSCRIPTION_ID})
    MERGE (owner)-[r:RESOURCE]->(log)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    """
    tx.run(
        query,
        LOGS=log_profiles_list,
        SUBSCRIPTION_ID=subscription_id,
        update_tag=update_tag,
    )
    for log_profile in log_profiles_list:
        resource_group=get_azure_resource_group_name(log_profile.get('id'))
        _attach_resource_group_monitor_logs(tx,log_profile['id'],resource_group,update_tag)


def _attach_resource_group_monitor_logs(tx: neo4j.Transaction, log_profile_id:str,resource_group:str ,update_tag: int) -> None:
    query = """
    MATCH (log:AzureMonitorLogProfile{id: $log_profile_id})
    WITH log
    MATCH (rg:AzureResourceGroup{name: $resource_group})
    MERGE (log)-[r:RESOURCE_GROUP]->(rg)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    """
    tx.run(
        query,
        log_profile_id=log_profile_id,
        resource_group=resource_group,
        update_tag=update_tag,
    )

def cleanup_monitor_log_profiles(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('azure_import_monitor_log_profiles_cleanup.json', neo4j_session, common_job_parameters)


def sync_monitor_log_profiles(
    neo4j_session: neo4j.Session, credentials: Credentials, subscription_id: str, update_tag: int,
    common_job_parameters: Dict, regions: list,
) -> None:
    client = get_monitoring_client(credentials, subscription_id)
    log_profiles = get_log_profiles_list(client, regions, common_job_parameters)
    log_profiles_list = transform_log_profiles(log_profiles, regions, common_job_parameters)

    load_monitor_log_profiles(neo4j_session, subscription_id, log_profiles_list, update_tag)
    cleanup_monitor_log_profiles(neo4j_session, common_job_parameters)


@timeit
def sync(
    neo4j_session: neo4j.Session, credentials: Credentials, subscription_id: str, update_tag: int,
    common_job_parameters: Dict, regions: list,
) -> None:
    logger.info("Syncing key Monitor Log Profiles for subscription '%s'.", subscription_id)

    sync_monitor_log_profiles(neo4j_session, credentials, subscription_id, update_tag, common_job_parameters, regions)
