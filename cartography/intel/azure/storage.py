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

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.azure.storage.account import AzureStorageAccountSchema
from cartography.models.azure.storage.blobcontainer import (
    AzureStorageBlobContainerSchema,
)
from cartography.models.azure.storage.blobservice import AzureStorageBlobServiceSchema
from cartography.models.azure.storage.fileservice import AzureStorageFileServiceSchema
from cartography.models.azure.storage.fileshare import AzureStorageFileShareSchema
from cartography.models.azure.storage.queue import AzureStorageQueueSchema
from cartography.models.azure.storage.queueservice import AzureStorageQueueServiceSchema
from cartography.models.azure.storage.table import AzureStorageTableSchema
from cartography.models.azure.storage.tableservice import AzureStorageTableServiceSchema
from cartography.models.azure.tags.storage_tag import AzureStorageTagsSchema
from cartography.util import timeit

from .util.credentials import Credentials
from .util.tag import transform_tags

logger = logging.getLogger(__name__)


@timeit
def get_client(
    credentials: Credentials,
    subscription_id: str,
) -> StorageManagementClient:
    """
    Getting the Azure Storage client
    """
    client = StorageManagementClient(credentials, subscription_id)
    return client


@timeit
def get_storage_account_list(
    credentials: Credentials,
    subscription_id: str,
) -> List[Dict]:
    """
    Getting the list of storage accounts
    """
    try:
        client = get_client(credentials, subscription_id)
        storage_account_list = list(
            map(lambda x: x.as_dict(), client.storage_accounts.list()),
        )

    # ClientAuthenticationError and ResourceNotFoundError are subclasses under HttpResponseError
    except ClientAuthenticationError as e:
        logger.warning(
            f"Client Authentication Error while retrieving storage accounts - {e}",
        )
        return []
    except ResourceNotFoundError as e:
        logger.warning(f"Storage Account not found error - {e}")
        return []
    except HttpResponseError as e:
        logger.warning(f"Error while retrieving storage accounts - {e}")
        return []

    for storage_account in storage_account_list:
        x = storage_account["id"].split("/")
        storage_account["resourceGroup"] = x[x.index("resourceGroups") + 1]

    return storage_account_list


@timeit
def load_storage_account_data(
    neo4j_session: neo4j.Session,
    subscription_id: str,
    storage_account_list: List[Dict],
    azure_update_tag: int,
) -> None:
    load(
        neo4j_session,
        AzureStorageAccountSchema(),
        storage_account_list,
        lastupdated=azure_update_tag,
        AZURE_SUBSCRIPTION_ID=subscription_id,
    )


@timeit
def load_storage_tags(
    neo4j_session: neo4j.Session,
    subscription_id: str,
    storage_accounts: List[Dict],
    update_tag: int,
) -> None:
    """
    Sync tags for storage accounts.
    """
    tags = transform_tags(storage_accounts, subscription_id)
    load(
        neo4j_session,
        AzureStorageTagsSchema(),
        tags,
        lastupdated=update_tag,
        AZURE_SUBSCRIPTION_ID=subscription_id,
    )


@timeit
def sync_storage_account_details(
    neo4j_session: neo4j.Session,
    credentials: Credentials,
    subscription_id: str,
    storage_account_list: List[Dict],
    sync_tag: int,
) -> None:
    # Get details
    details = get_storage_account_details(
        credentials,
        subscription_id,
        storage_account_list,
    )
    # Transform details
    queue_services, table_services, file_services, blob_services = (
        transform_storage_account_details(
            details,
        )
    )
    # Load details
    _load_queue_services(neo4j_session, queue_services, subscription_id, sync_tag)
    _load_table_services(neo4j_session, table_services, subscription_id, sync_tag)
    _load_file_services(neo4j_session, file_services, subscription_id, sync_tag)
    _load_blob_services(neo4j_session, blob_services, subscription_id, sync_tag)

    sync_queue_services_details(
        neo4j_session,
        credentials,
        subscription_id,
        queue_services,
        sync_tag,
    )
    sync_table_services_details(
        neo4j_session,
        credentials,
        subscription_id,
        table_services,
        sync_tag,
    )
    sync_file_services_details(
        neo4j_session,
        credentials,
        subscription_id,
        file_services,
        sync_tag,
    )
    sync_blob_services_details(
        neo4j_session,
        credentials,
        subscription_id,
        blob_services,
        sync_tag,
    )


@timeit
def get_storage_account_details(
    credentials: Credentials,
    subscription_id: str,
    storage_account_list: List[Dict],
) -> Generator[Any, Any, Any]:
    """
    Iterates over all Storage Accounts to get the different storage services.
    """
    for storage_account in storage_account_list:
        queue_services = get_queue_services(
            credentials,
            subscription_id,
            storage_account,
        )
        table_services = get_table_services(
            credentials,
            subscription_id,
            storage_account,
        )
        file_services = get_file_services(credentials, subscription_id, storage_account)
        blob_services = get_blob_services(credentials, subscription_id, storage_account)
        yield storage_account["id"], storage_account["name"], storage_account[
            "resourceGroup"
        ], queue_services, table_services, file_services, blob_services


@timeit
def get_queue_services(
    credentials: Credentials,
    subscription_id: str,
    storage_account: Dict,
) -> List[Dict]:
    """
    Gets the list of queue services.
    """
    try:
        client = get_client(credentials, subscription_id)
        queue_service_list = client.queue_services.list(
            storage_account["resourceGroup"],
            storage_account["name"],
        ).as_dict()["value"]

    except ClientAuthenticationError as e:
        logger.warning(
            f"Client Authentication Error while retrieving queue services - {e}",
        )
        return []
    except ResourceNotFoundError as e:
        logger.warning(f"Queue services resource not found error - {e}")
        return []
    except HttpResponseError as e:
        logger.warning(f"Error while retrieving queue services list - {e}")
        return []

    return queue_service_list


@timeit
def get_table_services(
    credentials: Credentials,
    subscription_id: str,
    storage_account: Dict,
) -> List[Dict]:
    """
    Gets the list of table services.
    """
    try:
        client = get_client(credentials, subscription_id)
        table_service_list = client.table_services.list(
            storage_account["resourceGroup"],
            storage_account["name"],
        ).as_dict()["value"]

    except ClientAuthenticationError as e:
        logger.warning(
            f"Client Authentication Error while retrieving table services - {e}",
        )
        return []
    except ResourceNotFoundError as e:
        logger.warning(f"Table services resource not found error - {e}")
        return []
    except HttpResponseError as e:
        logger.warning(f"Error while retrieving table services list - {e}")
        return []

    return table_service_list


@timeit
def get_file_services(
    credentials: Credentials,
    subscription_id: str,
    storage_account: Dict,
) -> List[Dict]:
    """
    Gets the list of file services.
    """
    try:
        client = get_client(credentials, subscription_id)
        file_service_list = client.file_services.list(
            storage_account["resourceGroup"],
            storage_account["name"],
        ).as_dict()["value"]

    except ClientAuthenticationError as e:
        logger.warning(
            f"Client Authentication Error while retrieving file services - {e}",
        )
        return []
    except ResourceNotFoundError as e:
        logger.warning(f"File services resource not found error - {e}")
        return []
    except HttpResponseError as e:
        logger.warning(f"Error while retrieving file services list - {e}")
        return []

    return file_service_list


@timeit
def get_blob_services(
    credentials: Credentials,
    subscription_id: str,
    storage_account: Dict,
) -> List[Dict]:
    """
    Gets the list of blob services.
    """
    try:
        client = get_client(credentials, subscription_id)
        blob_service_list = list(
            map(
                lambda x: x.as_dict(),
                client.blob_services.list(
                    storage_account["resourceGroup"],
                    storage_account["name"],
                ),
            ),
        )

    except ClientAuthenticationError as e:
        logger.warning(
            f"Client Authentication Error while retrieving blob services - {e}",
        )
        return []
    except ResourceNotFoundError as e:
        logger.warning(f"Blob services resource not found error - {e}")
        return []
    except HttpResponseError as e:
        logger.warning(f"Error while retrieving blob services list - {e}")
        return []

    return blob_service_list


@timeit
def transform_storage_account_details(
    storage_account_details: List[Tuple[Any, Any, Any, Any, Any, Any, Any]],
) -> Tuple[List[Dict], List[Dict], List[Dict], List[Dict]]:
    queue_services: List[Dict] = []
    table_services: List[Dict] = []
    file_services: List[Dict] = []
    blob_services: List[Dict] = []

    for (
        account_id,
        name,
        resourceGroup,
        queue_service,
        table_service,
        file_service,
        blob_service,
    ) in storage_account_details:
        if len(queue_service) > 0:
            for service in queue_service:
                service["storage_account_name"] = name
                service["storage_account_id"] = account_id
                service["resource_group_name"] = resourceGroup
            queue_services.extend(queue_service)

        if len(table_service) > 0:
            for service in table_service:
                service["storage_account_name"] = name
                service["storage_account_id"] = account_id
                service["resource_group_name"] = resourceGroup
            table_services.extend(table_service)

        if len(file_service) > 0:
            for service in file_service:
                service["storage_account_name"] = name
                service["storage_account_id"] = account_id
                service["resource_group_name"] = resourceGroup
            file_services.extend(file_service)

        if len(blob_service) > 0:
            for service in blob_service:
                service["storage_account_name"] = name
                service["storage_account_id"] = account_id
                service["resource_group_name"] = resourceGroup
            blob_services.extend(blob_service)
    return queue_services, table_services, file_services, blob_services


@timeit
def _load_queue_services(
    neo4j_session: neo4j.Session,
    queue_services: List[Dict],
    subscription_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        AzureStorageQueueServiceSchema(),
        queue_services,
        lastupdated=update_tag,
        AZURE_SUBSCRIPTION_ID=subscription_id,
    )


@timeit
def _load_table_services(
    neo4j_session: neo4j.Session,
    table_services: List[Dict],
    subscription_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        AzureStorageTableServiceSchema(),
        table_services,
        lastupdated=update_tag,
        AZURE_SUBSCRIPTION_ID=subscription_id,
    )


@timeit
def _load_file_services(
    neo4j_session: neo4j.Session,
    file_services: List[Dict],
    subscription_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        AzureStorageFileServiceSchema(),
        file_services,
        lastupdated=update_tag,
        AZURE_SUBSCRIPTION_ID=subscription_id,
    )


@timeit
def _load_blob_services(
    neo4j_session: neo4j.Session,
    blob_services: List[Dict],
    subscription_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        AzureStorageBlobServiceSchema(),
        blob_services,
        lastupdated=update_tag,
        AZURE_SUBSCRIPTION_ID=subscription_id,
    )


@timeit
def sync_queue_services_details(
    neo4j_session: neo4j.Session,
    credentials: Credentials,
    subscription_id: str,
    queue_services: List[Dict],
    update_tag: int,
) -> None:
    queue_services_details = get_queue_services_details(
        credentials,
        subscription_id,
        queue_services,
    )
    load_queue_services_details(
        neo4j_session, queue_services_details, subscription_id, update_tag
    )


@timeit
def get_queue_services_details(
    credentials: Credentials,
    subscription_id: str,
    queue_services: List[Dict],
) -> Generator[Any, Any, Any]:
    """
    Returning the queues with their respective queue service id.
    """
    for queue_service in queue_services:
        queues = get_queues(credentials, subscription_id, queue_service)
        yield queue_service["id"], queues


@timeit
def get_queues(
    credentials: Credentials,
    subscription_id: str,
    queue_service: Dict,
) -> List[Dict]:
    """
    Getting the queues from the queue service.
    """
    try:
        client = get_client(credentials, subscription_id)
        queues = list(
            map(
                lambda x: x.as_dict(),
                client.queue.list(
                    queue_service["resource_group_name"],
                    queue_service["storage_account_name"],
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
    neo4j_session: neo4j.Session,
    details: List[Tuple[Any, Any]],
    subscription_id: str,
    update_tag: int,
) -> None:
    """
    Create dictionary for the queue so we can import them in a single query
    """
    queues: List[Dict] = []

    for queue_service_id, queue in details:
        if len(queue) > 0:
            for q in queue:
                q["service_id"] = queue_service_id
            queues.extend(queue)

    _load_queues(neo4j_session, queues, subscription_id, update_tag)


@timeit
def _load_queues(
    neo4j_session: neo4j.Session,
    queues: List[Dict],
    subscription_id: str,
    update_tag: int,
) -> None:
    """
    Ingest Queue details into neo4j.
    """
    load(
        neo4j_session,
        AzureStorageQueueSchema(),
        queues,
        lastupdated=update_tag,
        AZURE_SUBSCRIPTION_ID=subscription_id,
    )


@timeit
def sync_table_services_details(
    neo4j_session: neo4j.Session,
    credentials: Credentials,
    subscription_id: str,
    table_services: List[Dict],
    update_tag: int,
) -> None:
    table_services_details = get_table_services_details(
        credentials,
        subscription_id,
        table_services,
    )
    load_table_services_details(
        neo4j_session, table_services_details, subscription_id, update_tag
    )


@timeit
def get_table_services_details(
    credentials: Credentials,
    subscription_id: str,
    table_services: List[Dict],
) -> Generator[Any, Any, Any]:
    """
    Returning the tables with their respective table service id.
    """
    for table_service in table_services:
        tables = get_tables(credentials, subscription_id, table_service)
        yield table_service["id"], tables


@timeit
def get_tables(
    credentials: Credentials,
    subscription_id: str,
    table_service: Dict,
) -> List[Dict]:
    """
    Getting the tables from the table service.
    """
    try:
        client = get_client(credentials, subscription_id)
        tables = list(
            map(
                lambda x: x.as_dict(),
                client.table.list(
                    table_service["resource_group_name"],
                    table_service["storage_account_name"],
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
    neo4j_session: neo4j.Session,
    details: List[Tuple[Any, Any]],
    subscription_id: str,
    update_tag: int,
) -> None:
    """
    Create dictionary for the table so we can import them in a single query
    """
    tables: List[Dict] = []

    for table_service_id, table in details:
        if len(table) > 0:
            for t in table:
                t["service_id"] = table_service_id
            tables.extend(table)

    _load_tables(neo4j_session, tables, subscription_id, update_tag)


@timeit
def _load_tables(
    neo4j_session: neo4j.Session,
    tables: List[Dict],
    subscription_id: str,
    update_tag: int,
) -> None:
    """
    Ingest Table details into neo4j.
    """
    load(
        neo4j_session,
        AzureStorageTableSchema(),
        tables,
        lastupdated=update_tag,
        AZURE_SUBSCRIPTION_ID=subscription_id,
    )


@timeit
def sync_file_services_details(
    neo4j_session: neo4j.Session,
    credentials: Credentials,
    subscription_id: str,
    file_services: List[Dict],
    update_tag: int,
) -> None:
    file_services_details = get_file_services_details(
        credentials,
        subscription_id,
        file_services,
    )
    load_file_services_details(
        neo4j_session, file_services_details, subscription_id, update_tag
    )


@timeit
def get_file_services_details(
    credentials: Credentials,
    subscription_id: str,
    file_services: List[Dict],
) -> Generator[Any, Any, Any]:
    """
    Returning the shares with their respective file service id.
    """
    for file_service in file_services:
        shares = get_shares(credentials, subscription_id, file_service)
        yield file_service["id"], shares


@timeit
def get_shares(
    credentials: Credentials,
    subscription_id: str,
    file_service: Dict,
) -> List[Dict]:
    """
    Getting the shares from the file service.
    """
    try:
        client = get_client(credentials, subscription_id)
        shares = list(
            map(
                lambda x: x.as_dict(),
                client.file_shares.list(
                    file_service["resource_group_name"],
                    file_service["storage_account_name"],
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
    neo4j_session: neo4j.Session,
    details: List[Tuple[Any, Any]],
    subscription_id: str,
    update_tag: int,
) -> None:
    """
    Create dictionary for the shares so we can import them in a single query
    """
    shares: List[Dict] = []

    for file_service_id, share in details:
        if len(share) > 0:
            for s in share:
                s["service_id"] = file_service_id
            shares.extend(share)

    _load_shares(neo4j_session, shares, subscription_id, update_tag)


@timeit
def _load_shares(
    neo4j_session: neo4j.Session,
    shares: List[Dict],
    subscription_id: str,
    update_tag: int,
) -> None:
    """
    Ingest Share details into neo4j.
    """
    load(
        neo4j_session,
        AzureStorageFileShareSchema(),
        shares,
        lastupdated=update_tag,
        AZURE_SUBSCRIPTION_ID=subscription_id,
    )


@timeit
def sync_blob_services_details(
    neo4j_session: neo4j.Session,
    credentials: Credentials,
    subscription_id: str,
    blob_services: List[Dict],
    update_tag: int,
) -> None:
    blob_services_details = get_blob_services_details(
        credentials,
        subscription_id,
        blob_services,
    )
    load_blob_services_details(
        neo4j_session, blob_services_details, subscription_id, update_tag
    )


@timeit
def get_blob_services_details(
    credentials: Credentials,
    subscription_id: str,
    blob_services: List[Dict],
) -> Generator[Any, Any, Any]:
    """
    Returning the blob containers with their respective blob service id.
    """
    for blob_service in blob_services:
        blob_containers = get_blob_containers(
            credentials,
            subscription_id,
            blob_service,
        )
        yield blob_service["id"], blob_containers


@timeit
def get_blob_containers(
    credentials: Credentials,
    subscription_id: str,
    blob_service: Dict,
) -> List[Dict]:
    """
    Getting the blob containers from the blob service.
    """
    try:
        client = get_client(credentials, subscription_id)
        blob_containers = list(
            map(
                lambda x: x.as_dict(),
                client.blob_containers.list(
                    blob_service["resource_group_name"],
                    blob_service["storage_account_name"],
                ),
            ),
        )

    except ClientAuthenticationError as e:
        logger.warning(
            f"Client Authentication Error while retrieving blob containers - {e}",
        )
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
    neo4j_session: neo4j.Session,
    details: List[Tuple[Any, Any]],
    subscription_id: str,
    update_tag: int,
) -> None:
    """
    Create dictionary for the blob containers so we can import them in a single query
    """
    blob_containers: List[Dict] = []

    for blob_service_id, container in details:
        if len(container) > 0:
            for c in container:
                c["service_id"] = blob_service_id
            blob_containers.extend(container)

    _load_blob_containers(neo4j_session, blob_containers, subscription_id, update_tag)


@timeit
def _load_blob_containers(
    neo4j_session: neo4j.Session,
    blob_containers: List[Dict],
    subscription_id: str,
    update_tag: int,
) -> None:
    """
    Ingest Blob Container details into neo4j.
    """
    load(
        neo4j_session,
        AzureStorageBlobContainerSchema(),
        blob_containers,
        lastupdated=update_tag,
        AZURE_SUBSCRIPTION_ID=subscription_id,
    )


@timeit
def cleanup_azure_storage_accounts(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict,
) -> None:
    for node in (
        AzureStorageAccountSchema,
        AzureStorageBlobServiceSchema,
        AzureStorageFileServiceSchema,
        AzureStorageQueueServiceSchema,
        AzureStorageTableServiceSchema,
        AzureStorageFileShareSchema,
        AzureStorageQueueSchema,
        AzureStorageTableSchema,
        AzureStorageBlobContainerSchema,
    ):
        GraphJob.from_node_schema(node(), common_job_parameters).run(
            neo4j_session,
        )


@timeit
def cleanup_azure_storage_tags(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict,
) -> None:
    """
    Delete stale Azure Storage Tags that are scoped to the current subscription.
    Uses the sub-resource relationship to only clean tags belonging to this subscription.
    """
    GraphJob.from_node_schema(AzureStorageTagsSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    credentials: Credentials,
    subscription_id: str,
    sync_tag: int,
    common_job_parameters: Dict,
) -> None:
    logger.info("Syncing Azure Storage for subscription '%s'.", subscription_id)
    storage_account_list = get_storage_account_list(credentials, subscription_id)
    load_storage_account_data(
        neo4j_session,
        subscription_id,
        storage_account_list,
        sync_tag,
    )
    load_storage_tags(neo4j_session, subscription_id, storage_account_list, sync_tag)
    sync_storage_account_details(
        neo4j_session,
        credentials,
        subscription_id,
        storage_account_list,
        sync_tag,
    )
    cleanup_azure_storage_accounts(neo4j_session, common_job_parameters)
    cleanup_azure_storage_tags(neo4j_session, common_job_parameters)
