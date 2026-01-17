import logging
from typing import Dict
from typing import List
from typing import Tuple

import neo4j
from azure.core.exceptions import HttpResponseError
from azure.mgmt.compute import ComputeManagementClient

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.azure.vm.datadisk import AzureDataDiskSchema
from cartography.models.azure.vm.disk import AzureDiskSchema
from cartography.models.azure.vm.snapshot import AzureSnapshotSchema
from cartography.models.azure.vm.virtualmachine import AzureVirtualMachineSchema
from cartography.util import timeit

from .util.credentials import Credentials

logger = logging.getLogger(__name__)


def get_client(
    credentials: Credentials,
    subscription_id: str,
) -> ComputeManagementClient:
    client = ComputeManagementClient(credentials, subscription_id)
    return client


def get_vm_list(credentials: Credentials, subscription_id: str) -> List[Dict]:
    try:
        client = get_client(credentials, subscription_id)
        vm_list = list(map(lambda x: x.as_dict(), client.virtual_machines.list_all()))

        for vm in vm_list:
            x = vm["id"].split("/")
            vm["resource_group"] = x[x.index("resourceGroups") + 1]

        return vm_list

    except HttpResponseError as e:
        logger.warning(f"Error while retrieving virtual machines - {e}")
        return []


def load_vms(
    neo4j_session: neo4j.Session,
    subscription_id: str,
    vm_list: List[Dict],
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        AzureVirtualMachineSchema(),
        vm_list,
        lastupdated=update_tag,
        AZURE_SUBSCRIPTION_ID=subscription_id,
    )


def load_vm_data_disks(
    neo4j_session: neo4j.Session,
    subscription_id: str,
    data_disks: List[Dict],
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        AzureDataDiskSchema(),
        data_disks,
        lastupdated=update_tag,
        AZURE_SUBSCRIPTION_ID=subscription_id,
    )


def cleanup_virtual_machine(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict,
) -> None:
    GraphJob.from_node_schema(AzureVirtualMachineSchema(), common_job_parameters).run(
        neo4j_session,
    )


def get_disks(credentials: Credentials, subscription_id: str) -> List[Dict]:
    try:
        client = get_client(credentials, subscription_id)
        disk_list = list(map(lambda x: x.as_dict(), client.disks.list()))

        for disk in disk_list:
            x = disk["id"].split("/")
            disk["resource_group"] = x[x.index("resourceGroups") + 1]

        return disk_list

    except HttpResponseError as e:
        logger.warning(f"Error while retrieving disks - {e}")
        return []


def load_disks(
    neo4j_session: neo4j.Session,
    subscription_id: str,
    disk_list: List[Dict],
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        AzureDiskSchema(),
        disk_list,
        lastupdated=update_tag,
        AZURE_SUBSCRIPTION_ID=subscription_id,
    )


def cleanup_disks(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    GraphJob.from_node_schema(AzureDiskSchema(), common_job_parameters).run(
        neo4j_session,
    )


def get_snapshots_list(credentials: Credentials, subscription_id: str) -> List[Dict]:
    try:
        client = get_client(credentials, subscription_id)
        snapshots = list(map(lambda x: x.as_dict(), client.snapshots.list()))

        for snapshot in snapshots:
            x = snapshot["id"].split("/")
            snapshot["resource_group"] = x[x.index("resourceGroups") + 1]

        return snapshots

    except HttpResponseError as e:
        logger.warning(f"Error while retrieving snapshots - {e}")
        return []


def load_snapshots(
    neo4j_session: neo4j.Session,
    subscription_id: str,
    snapshots: List[Dict],
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        AzureSnapshotSchema(),
        snapshots,
        lastupdated=update_tag,
        AZURE_SUBSCRIPTION_ID=subscription_id,
    )


def cleanup_snapshot(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    GraphJob.from_node_schema(AzureSnapshotSchema(), common_job_parameters).run(
        neo4j_session,
    )


def transform_vm_list(vm_list: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
    """
    Transform the VM list to separate the VMs and their data disks.
    """
    transformed_vm_list = []
    transformed_data_disk_list = []

    for vm in vm_list:
        for dd in vm.get("storage_profile", {}).get("data_disks", []):
            dd["vm_id"] = vm["id"]
            transformed_data_disk_list.append(dd)
        transformed_vm_list.append(vm)

    return transformed_vm_list, transformed_data_disk_list


def sync_virtual_machine(
    neo4j_session: neo4j.Session,
    credentials: Credentials,
    subscription_id: str,
    update_tag: int,
    common_job_parameters: Dict,
) -> None:
    vm_list = get_vm_list(credentials, subscription_id)
    transformed_vm_list, transformed_data_disk_list = transform_vm_list(vm_list)
    load_vms(neo4j_session, subscription_id, transformed_vm_list, update_tag)
    load_vm_data_disks(
        neo4j_session,
        subscription_id,
        transformed_data_disk_list,
        update_tag,
    )
    cleanup_virtual_machine(neo4j_session, common_job_parameters)


def sync_disk(
    neo4j_session: neo4j.Session,
    credentials: Credentials,
    subscription_id: str,
    update_tag: int,
    common_job_parameters: Dict,
) -> None:
    disk_list = get_disks(credentials, subscription_id)
    load_disks(neo4j_session, subscription_id, disk_list, update_tag)
    cleanup_disks(neo4j_session, common_job_parameters)


def sync_snapshot(
    neo4j_session: neo4j.Session,
    credentials: Credentials,
    subscription_id: str,
    update_tag: int,
    common_job_parameters: Dict,
) -> None:
    snapshots = get_snapshots_list(credentials, subscription_id)
    load_snapshots(neo4j_session, subscription_id, snapshots, update_tag)
    cleanup_snapshot(neo4j_session, common_job_parameters)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    credentials: Credentials,
    subscription_id: str,
    update_tag: int,
    common_job_parameters: Dict,
) -> None:
    logger.info("Syncing VM for subscription '%s'.", subscription_id)

    sync_virtual_machine(
        neo4j_session,
        credentials,
        subscription_id,
        update_tag,
        common_job_parameters,
    )
    sync_disk(
        neo4j_session,
        credentials,
        subscription_id,
        update_tag,
        common_job_parameters,
    )
    sync_snapshot(
        neo4j_session,
        credentials,
        subscription_id,
        update_tag,
        common_job_parameters,
    )
