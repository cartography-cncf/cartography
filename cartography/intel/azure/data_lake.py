import logging
from typing import Any

import neo4j
from azure.core.exceptions import ClientAuthenticationError
from azure.core.exceptions import HttpResponseError
from azure.mgmt.storage import StorageManagementClient

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.azure.data_lake_filesystem import AzureDataLakeFileSystemSchema
from cartography.util import timeit

from .util.credentials import Credentials

logger = logging.getLogger(__name__)


def _get_resource_group_from_id(resource_id: str) -> str:
    """
    Helper function to parse the resource group name from a full resource ID string.
    """
    parts = resource_id.lower().split("/")
    rg_index = parts.index("resourcegroups")
    return parts[rg_index + 1]


@timeit
def get_datalake_accounts(credentials: Credentials, subscription_id: str) -> list[dict]:
    try:
        client = StorageManagementClient(credentials.credential, subscription_id)
        storage_accounts = [sa.as_dict() for sa in client.storage_accounts.list()]
        return [sa for sa in storage_accounts if sa.get("is_hns_enabled")]
    except (ClientAuthenticationError, HttpResponseError) as e:
        logger.warning(f"Failed to get Storage Accounts for Data Lake sync: {str(e)}")
        return []


@timeit
def get_filesystems_for_account(
    client: StorageManagementClient,
    account: dict,
) -> list[dict]:
    resource_group_name = _get_resource_group_from_id(account["id"])
    try:
        return [
            c.as_dict()
            for c in client.blob_containers.list(
                resource_group_name,
                account["name"],
            )
        ]
    except (ClientAuthenticationError, HttpResponseError) as e:
        logger.warning(
            f"Failed to get containers for storage account {account['name']}: {str(e)}",
        )
        return []


@timeit
def transform_datalake_filesystems(filesystems_response: list[dict]) -> list[dict]:
    transformed_filesystems: list[dict[str, Any]] = []
    for fs in filesystems_response:
        transformed_filesystem = {
            "id": fs.get("id"),
            "name": fs.get("name"),
            "public_access": fs.get("properties", {}).get("public_access"),
            "last_modified_time": fs.get("properties", {}).get("last_modified_time"),
            "has_immutability_policy": fs.get("properties", {}).get(
                "has_immutability_policy",
            ),
            "has_legal_hold": fs.get("properties", {}).get("has_legal_hold"),
        }
        transformed_filesystems.append(transformed_filesystem)
    return transformed_filesystems


@timeit
def load_datalake_filesystems(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    storage_account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        AzureDataLakeFileSystemSchema(),
        data,
        lastupdated=update_tag,
        STORAGE_ACCOUNT_ID=storage_account_id,
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    credentials: Credentials,
    subscription_id: str,
    update_tag: int,
    common_job_parameters: dict,
) -> None:
    logger.info(
        f"Syncing Azure Data Lake File Systems for subscription {subscription_id}.",
    )
    client = StorageManagementClient(credentials.credential, subscription_id)

    datalake_accounts = get_datalake_accounts(credentials, subscription_id)
    for account in datalake_accounts:
        account_id = account["id"]
        raw_filesystems = get_filesystems_for_account(client, account)
        transformed_filesystems = transform_datalake_filesystems(raw_filesystems)

        load_datalake_filesystems(
            neo4j_session,
            transformed_filesystems,
            account_id,
            update_tag,
        )

        cleanup_params = common_job_parameters.copy()
        cleanup_params["STORAGE_ACCOUNT_ID"] = account_id
        GraphJob.from_node_schema(AzureDataLakeFileSystemSchema(), cleanup_params).run(
            neo4j_session,
        )
