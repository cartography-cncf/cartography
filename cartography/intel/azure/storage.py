import logging
from typing import Any
from typing import Dict
from typing import Generator
from typing import List
from typing import Tuple

import neo4j
from azure.core.exceptions import ClientAuthenticationError
from azure.core.exceptions import HttpResponseError
from azure.core.exceptions import ResourceNotFoundError
from azure.mgmt.storage import StorageManagementClient
from cloudconsolelink.clouds.azure import AzureLinker

from .util.credentials import Credentials
from cartography.util import get_azure_resource_group_name
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)
azure_console_link = AzureLinker()


@timeit
def get_client(credentials: Credentials, subscription_id: str) -> StorageManagementClient:
    """
    Getting the Azure Storage client
    """
    client = StorageManagementClient(credentials, subscription_id)
    return client


@timeit
def get_storage_account_list(credentials: Credentials, subscription_id: str, regions: list, common_job_parameters: Dict) -> List[Dict]:
    """
    Getting the list of storage accounts
    """
    try:
        client = get_client(credentials, subscription_id)
        storage_account_list = list(map(lambda x: x.as_dict(), client.storage_accounts.list()))

    # ClientAuthenticationError and ResourceNotFoundError are subclasses under HttpResponseError
    except ClientAuthenticationError as e:
        logger.warning(f"Client Authentication Error while retrieving storage accounts - {e}")
        return []
    except ResourceNotFoundError as e:
        logger.warning(f"Storage Account not found error - {e}")
        return []
    except HttpResponseError as e:
        logger.warning(f"Error while retrieving storage accounts - {e}")
        return []
    account_list = []
    for storage_account in storage_account_list:
        storage_account['resourceGroup'] = get_azure_resource_group_name(storage_account.get('id'))
        storage_account['allowBlobPublicAccess'] = storage_account.get(
            'properties', {},
        ).get('allow_blob_public_access', False)
        storage_account['consolelink'] = azure_console_link.get_console_link(
            id=storage_account['id'], primary_ad_domain_name=common_job_parameters['Azure_Primary_AD_Domain_Name'],
        )
        storage_account['location'] = storage_account.get('location', '').replace(" ", "").lower()
        if regions is None:
            account_list.append(storage_account)
        else:
            if storage_account.get('location') in regions or storage_account.get('location') == 'global':
                account_list.append(storage_account)
    return account_list


@timeit
def load_storage_account_data(
        neo4j_session: neo4j.Session, subscription_id: str, storage_account_list: List[Dict],
        azure_update_tag: int,
) -> None:
    """
    Ingest Storage Account details into neo4j.
    """
    ingest_storage_account = """
    UNWIND $storage_accounts_list as account
    MERGE (s:AzureStorageAccount{id: account.id})
    ON CREATE SET s.firstseen = timestamp(),
    s.type = account.type, s.resourcegroup = account.resourceGroup,
    s.location = account.location,
    s.region = account.location
    SET s.lastupdated = $azure_update_tag,
    s.kind = account.kind,
    s.name = account.name,
    s.consolelink = account.consolelink,
    s.creationtime = account.creation_time,
    s.hnsenabled = account.is_hns_enabled,
    s.primarylocation = account.primary_location,
    s.allowBlobPublicAccess = account.allowBlobPublicAccess,
    s.secondarylocation = account.secondary_location,
    s.provisioningstate = account.provisioning_state,
    s.statusofprimary = account.status_of_primary,
    s.statusofsecondary = account.status_of_secondary,
    s.supportshttpstrafficonly = account.enable_https_traffic_only,
    s.networkRuleDefaultAction = account.network_rule_set.default_action,
    s.region = account.location
    WITH s
    MATCH (owner:AzureSubscription{id: $AZURE_SUBSCRIPTION_ID})
    MERGE (owner)-[r:RESOURCE]->(s)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $azure_update_tag
    """

    neo4j_session.run(
        ingest_storage_account,
        storage_accounts_list=storage_account_list,
        AZURE_SUBSCRIPTION_ID=subscription_id,
        azure_update_tag=azure_update_tag,
    )
    for storage in storage_account_list:
        resource_group = get_azure_resource_group_name(storage.get('id'))
        _attach_resource_group_storage_account(neo4j_session, storage.get('id'), resource_group, azure_update_tag)


def _attach_resource_group_storage_account(neo4j_session: neo4j.Session, storage_account_id: str, resource_group: str, azure_update_tag: int) -> None:
    ingest_storage_account = """
    MATCH (s:AzureStorageAccount{id: $account_id})
    WITH s
    MATCH (rg:AzureResourceGroup{name: $resource_group})
    MERGE (s)-[r:RESOURCE_GROUP]->(rg)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $azure_update_tag
    """
    neo4j_session.run(
        ingest_storage_account,
        account_id=storage_account_id,
        resource_group=resource_group,
        azure_update_tag=azure_update_tag,
    )


@timeit
def sync_storage_account_details(
        neo4j_session: neo4j.Session, credentials: Credentials, subscription_id: str,
        storage_account_list: List[Dict], sync_tag: int, common_job_parameters: Dict,
) -> None:
    details = get_storage_account_details(credentials, subscription_id, storage_account_list, common_job_parameters)
    load_storage_account_details(neo4j_session, credentials, subscription_id, details, sync_tag, common_job_parameters)


@timeit
def get_storage_account_details(
        credentials: Credentials, subscription_id: str, storage_account_list: List[Dict], common_job_parameters: Dict,
) -> Generator[Any, Any, Any]:
    """
    Iterates over all Storage Accounts to get the different storage services.
    """
    for storage_account in storage_account_list:
        queue_services = get_queue_services(credentials, subscription_id, storage_account)
        table_services = get_table_services(credentials, subscription_id, storage_account)
        file_services = get_file_services(credentials, subscription_id, storage_account)
        blob_services = get_blob_services(credentials, subscription_id, storage_account)

        yield storage_account['id'], storage_account['name'], storage_account[
            'resourceGroup'
        ], queue_services, table_services, file_services, blob_services


@timeit
def get_queue_services(credentials: Credentials, subscription_id: str, storage_account: Dict) -> List[Dict]:
    """
    Gets the list of queue services.
    """
    try:
        client = get_client(credentials, subscription_id)
        queue_service_list = client.queue_services.list(
            storage_account['resourceGroup'], storage_account['name'],
        ).as_dict()['value']

    except ClientAuthenticationError as e:
        logger.warning(f"Client Authentication Error while retrieving queue services - {e}")
        return []
    except ResourceNotFoundError as e:
        logger.warning(f"Queue services resource not found error - {e}")
        return []
    except HttpResponseError as e:
        logger.warning(f"Error while retrieving queue services list - {e}")
        return []

    return queue_service_list


@timeit
def get_table_services(credentials: Credentials, subscription_id: str, storage_account: Dict) -> List[Dict]:
    """
    Gets the list of table services.
    """
    try:
        client = get_client(credentials, subscription_id)
        table_service_list = client.table_services.list(
            storage_account['resourceGroup'], storage_account['name'],
        ).as_dict()['value']

    except ClientAuthenticationError as e:
        logger.warning(f"Client Authentication Error while retrieving table services - {e}")
        return []
    except ResourceNotFoundError as e:
        logger.warning(f"Table services resource not found error - {e}")
        return []
    except HttpResponseError as e:
        logger.warning(f"Error while retrieving table services list - {e}")
        return []

    return table_service_list


@timeit
def get_file_services(credentials: Credentials, subscription_id: str, storage_account: Dict) -> List[Dict]:
    """
    Gets the list of file services.
    """
    try:
        client = get_client(credentials, subscription_id)
        file_service_list = client.file_services.list(
            storage_account['resourceGroup'], storage_account['name'],
        ).as_dict()['value']

    except ClientAuthenticationError as e:
        logger.warning(f"Client Authentication Error while retrieving file services - {e}")
        return []
    except ResourceNotFoundError as e:
        logger.warning(f"File services resource not found error - {e}")
        return []
    except HttpResponseError as e:
        logger.warning(f"Error while retrieving file services list - {e}")
        return []

    return file_service_list


@timeit
def get_blob_services(credentials: Credentials, subscription_id: str, storage_account: Dict) -> List[Dict]:
    """
    Gets the list of blob services.
    """
    try:
        client = get_client(credentials, subscription_id)
        blob_service_list = list(
            map(
                lambda x: x.as_dict(), client.blob_services.list(
                    storage_account['resourceGroup'],
                    storage_account['name'],
                ),
            ),
        )

    except ClientAuthenticationError as e:
        logger.warning(f"Client Authentication Error while retrieving blob services - {e}")
        return []
    except ResourceNotFoundError as e:
        logger.warning(f"Blob services resource not found error - {e}")
        return []
    except HttpResponseError as e:
        logger.warning(f"Error while retrieving blob services list - {e}")
        return []

    return blob_service_list


@timeit
def load_storage_account_details(
        neo4j_session: neo4j.Session, credentials: Credentials, subscription_id: str,
        details: List[Tuple[Any, Any, Any, Any, Any, Any, Any]], update_tag: int, common_job_parameters: Dict,
) -> None:
    """
    Create dictionaries for every Azure storage service so we can import them in a single query
    """
    queue_services: List[Dict] = []
    table_services: List[Dict] = []
    file_services: List[Dict] = []
    blob_services: List[Dict] = []

    for account_id, name, resourceGroup, queue_service, table_service, file_service, blob_service in details:
        if len(queue_service) > 0:
            for service in queue_service:
                service['storage_account_name'] = name
                service['storage_account_id'] = account_id
                service['resource_group_name'] = resourceGroup
                service['consolelink'] = azure_console_link.get_console_link(
                    id=service['id'], primary_ad_domain_name=common_job_parameters['Azure_Primary_AD_Domain_Name'],
                )
            queue_services.extend(queue_service)

        if len(table_service) > 0:
            for service in table_service:
                service['storage_account_name'] = name
                service['storage_account_id'] = account_id
                service['resource_group_name'] = resourceGroup
                service['consolelink'] = azure_console_link.get_console_link(
                    id=service['id'], primary_ad_domain_name=common_job_parameters['Azure_Primary_AD_Domain_Name'],
                )
            table_services.extend(table_service)

        if len(file_service) > 0:
            for service in file_service:
                service['storage_account_name'] = name
                service['storage_account_id'] = account_id
                service['resource_group_name'] = resourceGroup
                service['consolelink'] = azure_console_link.get_console_link(
                    id=service['id'], primary_ad_domain_name=common_job_parameters['Azure_Primary_AD_Domain_Name'],
                )
            file_services.extend(file_service)

        if len(blob_service) > 0:
            for service in blob_service:
                service['storage_account_name'] = name
                service['storage_account_id'] = account_id
                service['resource_group_name'] = resourceGroup
                service['consolelink'] = azure_console_link.get_console_link(
                    id=service['id'], primary_ad_domain_name=common_job_parameters['Azure_Primary_AD_Domain_Name'],
                )
            blob_services.extend(blob_service)

    _load_queue_services(neo4j_session, queue_services, update_tag)
    _load_table_services(neo4j_session, table_services, update_tag)
    _load_file_services(neo4j_session, file_services, update_tag)
    _load_blob_services(neo4j_session, blob_services, update_tag)

    sync_queue_services_details(neo4j_session, credentials, subscription_id, queue_services, update_tag, common_job_parameters)
    sync_table_services_details(neo4j_session, credentials, subscription_id, table_services, update_tag, common_job_parameters)
    sync_file_services_details(neo4j_session, credentials, subscription_id, file_services, update_tag, common_job_parameters)
    sync_blob_services_details(neo4j_session, credentials, subscription_id, blob_services, update_tag, common_job_parameters)


@timeit
def _load_queue_services(
        neo4j_session: neo4j.Session, queue_services: List[Dict], update_tag: int,
) -> None:
    """
    Ingest Queue Service details into neo4j.
    """
    ingest_queue_services = """
    UNWIND $queue_services_list as qservice
    MERGE (qs:AzureStorageQueueService{id: qservice.id})
    ON CREATE SET qs.firstseen = timestamp(), qs.type = qservice.type, qs.region = $region
    SET qs.name = qservice.name,
    qs.consolelink = qservice.consolelink,
    qs.region = $region,
    qs.lastupdated = $azure_update_tag
    WITH qs, qservice
    MATCH (s:AzureStorageAccount{id: qservice.storage_account_id})
    MERGE (s)-[r:USES]->(qs)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $azure_update_tag
    """

    neo4j_session.run(
        ingest_queue_services,
        region="global",
        queue_services_list=queue_services,
        azure_update_tag=update_tag,
    )
    for queue_service in queue_services:
        resource_group = get_azure_resource_group_name(queue_service.get('id'))
        _attach_resource_queue_service(neo4j_session, queue_service['id'], resource_group, update_tag)


def _attach_resource_queue_service(neo4j_session: neo4j.Session, queue_service_id: str, resource_group: str, update_tag: int) -> None:
    ingest_queue_services = """
    MATCH (qs:AzureStorageQueueService{id: $queue_service_id})
    WITH qs
    MATCH (rg:AzureResourceGroup{name: $resource_group})
    MERGE (qs)-[r:RESOURCE_GROUP]->(rg)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $azure_update_tag
    """
    neo4j_session.run(
        ingest_queue_services,
        queue_service_id=queue_service_id,
        resource_group=resource_group,
        azure_update_tag=update_tag,
    )


@timeit
def _load_table_services(
        neo4j_session: neo4j.Session, table_services: List[Dict], update_tag: int,
) -> None:
    """
    Ingest Table Service details into neo4j.
    """
    ingest_table_services = """
    UNWIND $table_services_list as tservice
    MERGE (ts:AzureStorageTableService{id: tservice.id})
    ON CREATE SET ts.firstseen = timestamp(), ts.type = tservice.type, ts.region = $region
    SET ts.name = tservice.name,
    ts.consolelink = tservice.consolelink,
    ts.region = $region,
    ts.lastupdated = $azure_update_tag
    WITH ts, tservice
    MATCH (s:AzureStorageAccount{id: tservice.storage_account_id})
    MERGE (s)-[r:USES]->(ts)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $azure_update_tag
    """

    neo4j_session.run(
        ingest_table_services,
        region="global",
        table_services_list=table_services,
        azure_update_tag=update_tag,
    )
    for table_service in table_services:
        resource_group = get_azure_resource_group_name(table_service.get('id'))
        _attach_resource_storage_table_service(neo4j_session, table_service['id'], resource_group, update_tag)


def _attach_resource_storage_table_service(neo4j_session: neo4j.Session, table_service_id: str, resource_group: str, update_tag: int) -> None:
    ingest_table_services = """
    MATCH (ts:AzureStorageTableService{id: $tservice_id})
    WITH ts
    MATCH (rg:AzureResourceGroup{name: $resource_group})
    MERGE (ts)-[r:RESOURCE_GROUP]->(rg)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $azure_update_tag
    """

    neo4j_session.run(
        ingest_table_services,
        tservice_id=table_service_id,
        resource_group=resource_group,
        azure_update_tag=update_tag,
    )


@timeit
def _load_file_services(
        neo4j_session: neo4j.Session, file_services: List[Dict], update_tag: int,
) -> None:
    """
    Ingest File Service details into neo4j.
    """
    ingest_file_services = """
    UNWIND $file_services_list as fservice
    MERGE (fs:AzureStorageFileService{id: fservice.id})
    ON CREATE SET fs.firstseen = timestamp(), fs.type = fservice.type, fs.region = $region
    SET fs.name = fservice.name,
    fs.consolelink = fservice.consolelink,
    fs.region = $region,
    fs.lastupdated = $azure_update_tag
    WITH fs, fservice
    MATCH (s:AzureStorageAccount{id: fservice.storage_account_id})
    MERGE (s)-[r:USES]->(fs)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $azure_update_tag
    """

    neo4j_session.run(
        ingest_file_services,
        region="global",
        file_services_list=file_services,
        azure_update_tag=update_tag,
    )
    for file_service in file_services:
        resource_group = get_azure_resource_group_name(file_service.get('id'))
        _attach_resource_storage_file_service(neo4j_session, file_service['id'], resource_group, update_tag)


def _attach_resource_storage_file_service(neo4j_session: neo4j.Session, file_service_id: str, resource_group: str, update_tag: int) -> None:
    ingest_file_services = """
    MATCH (fs:AzureStorageFileService{id: $fservice_id})
    WITH fs
    MATCH (rg:AzureResourceGroup{name: $resource_group})
    MERGE (fs)-[r:RESOURCE_GROUP]->(rg)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $azure_update_tag
    """
    neo4j_session.run(
        ingest_file_services,
        fservice_id=file_service_id,
        resource_group=resource_group,
        azure_update_tag=update_tag,
    )


@timeit
def _load_blob_services(
        neo4j_session: neo4j.Session, blob_services: List[Dict], update_tag: int,
) -> None:
    """
    Ingest Blob Service details into neo4j.
    """
    ingest_blob_services = """
    UNWIND $blob_services_list as bservice
    MERGE (bs:AzureStorageBlobService{id: bservice.id})
    ON CREATE SET bs.firstseen = timestamp(), bs.type = bservice.type, bs.region = $region
    SET bs.name = bservice.name,
    bs.consolelink = bservice.consolelink,
    bs.region = $region,
    bs.lastupdated = $azure_update_tag
    WITH bs, bservice
    MATCH (s:AzureStorageAccount{id: bservice.storage_account_id})
    MERGE (s)-[r:USES]->(bs)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $azure_update_tag
    """

    neo4j_session.run(
        ingest_blob_services,
        region="global",
        blob_services_list=blob_services,
        azure_update_tag=update_tag,
    )
    for blob_service in blob_services:
        resource_group = get_azure_resource_group_name(blob_service.get('id'))
        _attach_resource_storage_blob_service(neo4j_session, blob_service['id'], resource_group, update_tag)


def _attach_resource_storage_blob_service(neo4j_session: neo4j.Session, blob_service_id: str, resource_group: str, update_tag: int) -> None:
    ingest_blob_services = """
    MATCH (bs:AzureStorageBlobService{id: $bservice_id})
    WITH bs
    MATCH (rg:AzureResourceGroup{name: $resource_group})
    MERGE (bs)-[r:RESOURCE_GROUP]->(rg)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $azure_update_tag
    """
    neo4j_session.run(
        ingest_blob_services,
        bservice_id=blob_service_id,
        resource_group=resource_group,
        azure_update_tag=update_tag,
    )


@timeit
def sync_queue_services_details(
        neo4j_session: neo4j.Session, credentials: Credentials, subscription_id: str,
        queue_services: List[Dict], update_tag: int, common_job_parameters: Dict,
) -> None:
    queue_services_details = get_queue_services_details(credentials, subscription_id, queue_services)
    load_queue_services_details(neo4j_session, queue_services_details, update_tag, common_job_parameters)


@timeit
def get_queue_services_details(
        credentials: Credentials, subscription_id: str, queue_services: List[Dict],
) -> Generator[Any, Any, Any]:
    """
    Returning the queues with their respective queue service id.
    """
    for queue_service in queue_services:
        queues = get_queues(credentials, subscription_id, queue_service)
        yield queue_service['id'], queues


@timeit
def get_queues(credentials: Credentials, subscription_id: str, queue_service: Dict) -> List[Dict]:
    """
    Getting the queues from the queue service.
    """
    try:
        client = get_client(credentials, subscription_id)
        queues = list(
            map(
                lambda x: x.as_dict(), client.queue.list(
                    queue_service['resource_group_name'],
                    queue_service['storage_account_name'],
                ),
            ),
        )

    except ClientAuthenticationError as e:
        logger.warning(f"Client Authentication Error while retrieving queues - {e}")
        return []
    except ResourceNotFoundError as e:
        logger.warning(f"Queue resource not found error - {e}")
        return []
    except HttpResponseError as e:
        logger.warning(f"Error while retrieving queues - {e}")
        return []

    return queues


@timeit
def load_queue_services_details(
        neo4j_session: neo4j.Session, details: List[Tuple[Any, Any]], update_tag: int, common_job_parameters: Dict,
) -> None:
    """
    Create dictionary for the queue so we can import them in a single query
    """
    queues: List[Dict] = []

    for queue_service_id, queue in details:
        if len(queue) > 0:
            for q in queue:
                q['service_id'] = queue_service_id
                q['consolelink'] = azure_console_link.get_console_link(
                    id=q['id'],
                    primary_ad_domain_name=common_job_parameters['Azure_Primary_AD_Domain_Name'],
                )
            queues.extend(queue)

    _load_queues(neo4j_session, queues, update_tag)


@timeit
def _load_queues(neo4j_session: neo4j.Session, queues: List[Dict], update_tag: int) -> None:
    """
    Ingest Queue details into neo4j.
    """
    ingest_queues = """
    UNWIND $queues_list as queue
    MERGE (q:AzureStorageQueue{id: queue.id})
    ON CREATE SET q.firstseen = timestamp(), q.type = queue.type, q.region = $region
    SET q.name = queue.name,
    q.region = $region,
    q.consolelink = queue.consolelink,
    q.lastupdated = $azure_update_tag
    WITH q, queue
    MATCH (qs:AzureStorageQueueService{id: queue.service_id})
    MERGE (qs)-[r:CONTAINS]->(q)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $azure_update_tag
    """

    neo4j_session.run(
        ingest_queues,
        region="global",
        queues_list=queues,
        azure_update_tag=update_tag,
    )
    for queue in queues:
        resource_group = get_azure_resource_group_name(queue.get('id'))
        _attach_resource_storage_queue(neo4j_session, queue['id'], resource_group, update_tag)


def _attach_resource_storage_queue(neo4j_session: neo4j.Session, queue_id: str, resource_group: str, update_tag: int) -> None:
    ingest_queues = """
    MATCH (q:AzureStorageQueue{id: $queue_id})
    WITH q
    MATCH (rg:AzureResourceGroup{name: $resource_group})
    MERGE (q)-[r:RESOURCE_GROUP]->(rg)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $azure_update_tag
    """

    neo4j_session.run(
        ingest_queues,
        queue_id=queue_id,
        resource_group=resource_group,
        azure_update_tag=update_tag,
    )


@timeit
def sync_table_services_details(
        neo4j_session: neo4j.Session, credentials: Credentials, subscription_id: str,
        table_services: List[Dict], update_tag: int, common_job_parameters: Dict,
) -> None:
    table_services_details = get_table_services_details(credentials, subscription_id, table_services)
    load_table_services_details(neo4j_session, table_services_details, update_tag, common_job_parameters)


@timeit
def get_table_services_details(
        credentials: Credentials, subscription_id: str, table_services: List[Dict],
) -> Generator[Any, Any, Any]:
    """
    Returning the tables with their respective table service id.
    """
    for table_service in table_services:
        tables = get_tables(credentials, subscription_id, table_service)
        yield table_service['id'], tables


@timeit
def get_tables(credentials: Credentials, subscription_id: str, table_service: Dict) -> List[Dict]:
    """
    Getting the tables from the table service.
    """
    try:
        client = get_client(credentials, subscription_id)
        tables = list(
            map(
                lambda x: x.as_dict(), client.table.list(
                    table_service['resource_group_name'],
                    table_service['storage_account_name'],
                ),
            ),
        )

    except ClientAuthenticationError as e:
        logger.warning(f"Client Authentication Error while retrieving tables - {e}")
        return []
    except ResourceNotFoundError as e:
        logger.warning(f"Table resource not found error - {e}")
        return []
    except HttpResponseError as e:
        logger.warning(f"Error while retrieving tables - {e}")
        return []

    return tables


@timeit
def load_table_services_details(
        neo4j_session: neo4j.Session, details: List[Tuple[Any, Any]], update_tag: int, common_job_parameters: Dict,
) -> None:
    """
    Create dictionary for the table so we can import them in a single query
    """
    tables: List[Dict] = []

    for table_service_id, table in details:
        if len(table) > 0:
            for t in table:
                t['service_id'] = table_service_id
                t['consolelink'] = azure_console_link.get_console_link(
                    id=t['id'],
                    primary_ad_domain_name=common_job_parameters['Azure_Primary_AD_Domain_Name'],
                )
            tables.extend(table)

    _load_tables(neo4j_session, tables, update_tag)


@timeit
def _load_tables(neo4j_session: neo4j.Session, tables: List[Dict], update_tag: int) -> None:
    """
    Ingest Table details into neo4j.
    """
    ingest_tables = """
    UNWIND $tables_list as table
    MERGE (t:AzureStorageTable{id: table.id})
    ON CREATE SET t.firstseen = timestamp(), t.type = table.type, t.region = $region
    SET t.name = table.name,
    t.region = $region,
    t.consolelink = table.consolelink,
    t.tablename = table.table_name,
    t.lastupdated = $azure_update_tag
    WITH t, table
    MATCH (ts:AzureStorageTableService{id: table.service_id})
    MERGE (ts)-[r:CONTAINS]->(t)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $azure_update_tag
    """

    neo4j_session.run(
        ingest_tables,
        region="global",
        tables_list=tables,
        azure_update_tag=update_tag,
    )
    for table in tables:
        resource_group = get_azure_resource_group_name(table.get('id'))
        _attach_resource_storage_table(neo4j_session, table['id'], resource_group, update_tag)


def _attach_resource_storage_table(neo4j_session: neo4j.Session, table_id: str, resource_group: str, update_tag: int) -> None:
    """
    Ingest Table details into neo4j.
    """
    ingest_tables = """
    MATCH (t:AzureStorageTable{id: $table_id})
    WITH t
    MATCH (rg:AzureResourceGroup{name: $resource_group})
    MERGE (t)-[r:RESOURCE_GROUP]->(rg)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $azure_update_tag
    """

    neo4j_session.run(
        ingest_tables,
        table_id=table_id,
        resource_group=resource_group,
        azure_update_tag=update_tag,
    )


@timeit
def sync_file_services_details(
        neo4j_session: neo4j.Session, credentials: Credentials, subscription_id: str,
        file_services: List[Dict], update_tag: int, common_job_parameters: Dict,
) -> None:
    file_services_details = get_file_services_details(credentials, subscription_id, file_services)
    load_file_services_details(neo4j_session, file_services_details, update_tag, common_job_parameters)


@timeit
def get_file_services_details(
        credentials: Credentials, subscription_id: str, file_services: List[Dict],
) -> Generator[Any, Any, Any]:
    """
    Returning the shares with their respective file service id.
    """
    for file_service in file_services:
        shares = get_shares(credentials, subscription_id, file_service)
        yield file_service['id'], shares


@timeit
def get_shares(credentials: Credentials, subscription_id: str, file_service: Dict) -> List[Dict]:
    """
    Getting the shares from the file service.
    """
    try:
        client = get_client(credentials, subscription_id)
        shares = list(
            map(
                lambda x: x.as_dict(), client.file_shares.list(
                    file_service['resource_group_name'],
                    file_service['storage_account_name'],
                ),
            ),
        )

    except ClientAuthenticationError as e:
        logger.warning(f"Client Authentication Error while retrieving tables - {e}")
        return []
    except ResourceNotFoundError as e:
        logger.warning(f"Table resource not found error - {e}")
        return []
    except HttpResponseError as e:
        logger.warning(f"Error while retrieving file shares - {e}")
        return []

    return shares


@timeit
def load_file_services_details(
        neo4j_session: neo4j.Session, details: List[Tuple[Any, Any]], update_tag: int, common_job_parameters: Dict,
) -> None:
    """
    Create dictionary for the shares so we can import them in a single query
    """
    shares: List[Dict] = []

    for file_service_id, share in details:
        if len(share) > 0:
            for s in share:
                s['service_id'] = file_service_id
                s['consolelink'] = azure_console_link.get_console_link(
                    id=s['id'],
                    primary_ad_domain_name=common_job_parameters['Azure_Primary_AD_Domain_Name'],
                )
            shares.extend(share)

    _load_shares(neo4j_session, shares, update_tag)


@timeit
def _load_shares(neo4j_session: neo4j.Session, shares: List[Dict], update_tag: int) -> None:
    """
    Ingest Share details into neo4j.
    """
    ingest_shares = """
    UNWIND $shares_list as s
    MERGE (share:AzureStorageFileShare{id: s.id})
    ON CREATE SET share.firstseen = timestamp(), share.type = s.type, share.region = $region
    SET share.name = s.name,
    share.lastupdated = $azure_update_tag,
    share.lastmodifiedtime = s.last_modified_time,
    share.region = $region,
    share.sharequota = s.share_quota,
    share.accesstier = s.access_tier,
    share.consolelink = s.consolelink,
    share.deleted = s.deleted,
    share.accesstierchangetime = s.access_tier_change_time,
    share.accesstierstatus = s.access_tier_status,
    share.deletedtime = s.deleted_time,
    share.enabledprotocols = s.enabled_protocols,
    share.remainingretentiondays = s.remaining_retention_days,
    share.shareusagebytes = s.share_usage_bytes,
    share.version = s.version
    WITH share, s
    MATCH (fs:AzureStorageFileService{id: s.service_id})
    MERGE (fs)-[r:CONTAINS]->(share)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $azure_update_tag
    """

    neo4j_session.run(
        ingest_shares,
        region="global",
        shares_list=shares,
        azure_update_tag=update_tag,
    )
    for share in shares:
        resource_group = get_azure_resource_group_name(share.get('id'))
        _attach_resource_storage_share(neo4j_session, share['id'], resource_group, update_tag)


def _attach_resource_storage_share(neo4j_session: neo4j.Session, share_id: str, resource_group: str, update_tag: int) -> None:
    ingest_shares = """
    MATCH (share:AzureStorageFileShare{id: $share_id})
    WITH share
    MATCH (rg:AzureResourceGroup{name:$resource_group})
    MERGE (share)-[r:RESOURCE_GROUP]->(rg)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $azure_update_tag
    """
    neo4j_session.run(
        ingest_shares,
        share_id=share_id,
        resource_group=resource_group,
        azure_update_tag=update_tag,
    )


@timeit
def sync_blob_services_details(
        neo4j_session: neo4j.Session, credentials: Credentials, subscription_id: str,
        blob_services: List[Dict], update_tag: int, common_job_parameters: Dict,
) -> None:
    blob_services_details = get_blob_services_details(credentials, subscription_id, blob_services)
    load_blob_services_details(neo4j_session, blob_services_details, update_tag, common_job_parameters)


@timeit
def get_blob_services_details(
        credentials: Credentials, subscription_id: str, blob_services: List[Dict],
) -> Generator[Any, Any, Any]:
    """
    Returning the blob containers with their respective blob service id.
    """
    for blob_service in blob_services:
        blob_containers = get_blob_containers(credentials, subscription_id, blob_service)
        yield blob_service['id'], blob_containers


@timeit
def get_blob_containers(credentials: Credentials, subscription_id: str, blob_service: Dict) -> List[Dict]:
    """
    Getting the blob containers from the blob service.
    """
    try:
        client = get_client(credentials, subscription_id)
        blob_containers = list(
            map(
                lambda x: x.as_dict(),
                client.blob_containers.list(
                    blob_service['resource_group_name'],
                    blob_service['storage_account_name'],
                ),
            ),
        )

    except ClientAuthenticationError as e:
        logger.warning(f"Client Authentication Error while retrieving blob containers - {e}")
        return []
    except ResourceNotFoundError as e:
        logger.warning(f"Blob containers resource not found error - {e}")
        return []
    except HttpResponseError as e:
        logger.warning(f"Error while retrieving blob containers - {e}")
        return []

    return blob_containers


@timeit
def load_blob_services_details(
        neo4j_session: neo4j.Session, details: List[Tuple[Any, Any]], update_tag: int, common_job_parameters: Dict,
) -> None:
    """
    Create dictionary for the blob containers so we can import them in a single query
    """
    blob_containers: List[Dict] = []

    for blob_service_id, container in details:
        if len(container) > 0:
            for c in container:
                c['service_id'] = blob_service_id
                c['consolelink'] = azure_console_link.get_console_link(
                    id=c['id'],
                    primary_ad_domain_name=common_job_parameters['Azure_Primary_AD_Domain_Name'],
                )
                c['public_access'] = c['public_access'].lower()
            blob_containers.extend(container)

    _load_blob_containers(neo4j_session, blob_containers, update_tag)


@timeit
def _load_blob_containers(
        neo4j_session: neo4j.Session, blob_containers: List[Dict], update_tag: int,
) -> None:
    """
    Ingest Blob Container details into neo4j.
    """
    ingest_blob_containers = """
    UNWIND $blob_containers_list as blob
    MERGE (bc:AzureStorageBlobContainer{id: blob.id})
    ON CREATE SET bc.firstseen = timestamp(), bc.type = blob.type, bc.region = $region
    SET bc.name = blob.name,
    bc.lastupdated = $azure_update_tag,
    bc.deleted = blob.deleted,
    bc.deletedtime = blob.deleted_time,
    bc.region = $region,
    bc.defaultencryptionscope = blob.default_encryption_scope,
    bc.publicaccess = blob.public_access,
    bc.leasestatus = blob.lease_status,
    bc.consolelink = blob.consolelink,
    bc.leasestate = blob.lease_state,
    bc.lastmodifiedtime = blob.last_modified_time,
    bc.remainingretentiondays = blob.remaining_retention_days,
    bc.version = blob.version,
    bc.hasimmutabilitypolicy = blob.has_immutability_policy,
    bc.haslegalhold = blob.has_legal_hold,
    bc.leaseduration = blob.leaseDuration
    WITH bc, blob
    MATCH (bs:AzureStorageBlobService{id: blob.service_id})
    MERGE (bs)-[r:CONTAINS]->(bc)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $azure_update_tag
    """

    neo4j_session.run(
        ingest_blob_containers,
        region="global",
        blob_containers_list=blob_containers,
        azure_update_tag=update_tag,
    )
    for blob_container in blob_containers:
        resource_group = get_azure_resource_group_name(blob_container.get('id'))
        _attach_resource_storage_blob_container(neo4j_session, blob_container['id'], resource_group, update_tag)


def _attach_resource_storage_blob_container(neo4j_session: neo4j.Session, blob_container_id: str, resource_group: str, update_tag: int) -> None:
    ingest_blob_containers = """
    MATCH (bc:AzureStorageBlobContainer{id: $blob_id})
    WITH bc
    MATCH (rg:AzureResourceGroup{name: $resource_group})
    MERGE (bc)-[r:RESOURCE_GROUP]->(rg)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $azure_update_tag
    """
    neo4j_session.run(
        ingest_blob_containers,
        blob_id=blob_container_id,
        resource_group=resource_group,
        azure_update_tag=update_tag,
    )


@timeit
def cleanup_azure_storage_accounts(
        neo4j_session: neo4j.Session, common_job_parameters: Dict,
) -> None:
    run_cleanup_job('azure_storage_account_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync(
        neo4j_session: neo4j.Session, credentials: Credentials, subscription_id: str,
        sync_tag: int, common_job_parameters: Dict, regions: list,
) -> None:
    logger.info("Syncing Azure Storage for subscription '%s'.", subscription_id)
    storage_account_list = get_storage_account_list(credentials, subscription_id, regions, common_job_parameters)
    load_storage_account_data(neo4j_session, subscription_id, storage_account_list, sync_tag)
    sync_storage_account_details(
        neo4j_session, credentials, subscription_id,
        storage_account_list, sync_tag, common_job_parameters,
    )
    cleanup_azure_storage_accounts(neo4j_session, common_job_parameters)
