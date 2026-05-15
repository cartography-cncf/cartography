import logging
from typing import Dict
from typing import List

import neo4j
from azure.core.exceptions import HttpResponseError
from azure.mgmt.compute import ComputeManagementClient
from cloudconsolelink.clouds.azure import AzureLinker

from . import vmss
from .util.credentials import Credentials
from cartography.data.operating_systems import OPERATING_SYSTEMS
from cartography.util import get_azure_resource_group_name
from cartography.util import run_cleanup_job
from cartography.util import timeit
logger = logging.getLogger(__name__)
azure_console_link = AzureLinker()


def load_vm_extensions(session: neo4j.Session, data_list: List[Dict], update_tag: int) -> None:
    session.execute_write(_load_vm_extensions_tx, data_list, update_tag)


def load_vm_available_sizes(session: neo4j.Session, data_list: List[Dict], update_tag: int) -> None:
    session.execute_write(_load_vm_available_sizes_tx, data_list, update_tag)


def load_vm_scale_sets(session: neo4j.Session, subscription_id: str, data_list: List[Dict], update_tag: int) -> None:
    session.execute_write(_load_vm_scale_sets_tx, subscription_id, data_list, update_tag)


def load_vm_scale_sets_extensions(session: neo4j.Session, data_list: List[Dict], update_tag: int) -> None:
    session.execute_write(_load_vm_scale_sets_extensions_tx, data_list, update_tag)


def load_vm_security_groups_relationship(session: neo4j.Session, vm_id: str, data_list: List[Dict], update_tag: int) -> None:  # noqa: E501
    session.execute_write(_load_vm_security_groups_relationship, vm_id, data_list, update_tag)


def load_vm_network_interfaces_relationship(session: neo4j.Session, vm_id: str, data_list: List[Dict], update_tag: int) -> None:  # noqa: E501
    session.execute_write(_load_vm_network_interfaces_relationship, vm_id, data_list, update_tag)


def get_client(credentials: Credentials, subscription_id: str) -> ComputeManagementClient:
    client = ComputeManagementClient(credentials, subscription_id)
    return client


def _extract_aks_tags(tags_dict) -> Dict:
    if not tags_dict:
        return {'aks_cluster_name': None, 'aks_pool_name': None, 'aks_cluster_rg': None}

    # Lowercase keys for safe lookup
    lower_tags = {k.lower(): v for k, v in tags_dict.items()}
    return {
        'aks_cluster_name': lower_tags.get('aks-managed-cluster-name'),
        'aks_pool_name': lower_tags.get('aks-managed-poolname'),
        'aks_cluster_rg': lower_tags.get('aks-managed-cluster-rg'),
    }


def get_vm_list(credentials: Credentials, subscription_id: str, regions: list, common_job_parameters: Dict) -> List[Dict]:  # noqa: E501
    try:
        client = get_client(credentials, subscription_id)
        vm_list = list(map(lambda x: x.as_dict(), client.virtual_machines.list_all()))
        vm_data = []
        for vm in vm_list:
            vm['resource_group'] = get_azure_resource_group_name(vm.get('id'))
            vm['consolelink'] = azure_console_link.get_console_link(
                id=vm['id'], primary_ad_domain_name=common_job_parameters['Azure_Primary_AD_Domain_Name'],
            )
            aks_tags = _extract_aks_tags(vm.get('tags', {}))
            vm['aks_cluster_name'] = aks_tags['aks_cluster_name']
            vm['aks_pool_name'] = aks_tags['aks_pool_name']
            vm['aks_cluster_rg'] = aks_tags['aks_cluster_rg']
            network_interfaces = []
            for interface in vm.get('network_profile', {}).get('network_interfaces', []):
                network_interfaces.append(interface)
            vm['network_interfaces'] = network_interfaces
            vm['user_assigned_identities'] = list(vm.get('identity', {}).get('user_assigned_identities', {}).keys())
            network_security_group = []
            for config in vm.get('network_profile', {}).get('network_interface_configurations', []):
                network_security_group.append(config.get('network_security_group'), None)
            vm['network_security_group'] = network_security_group

            os_disk = vm.get("storage_profile", {}).get("os_disk", {})
            vm['os_type'] = os_disk.get('os_type')
            vm['os_disk_name'] = os_disk.get('name')
            vm['is_spot_instance'] = str(vm.get('priority', '')).lower() == 'spot'
            image_reference = vm.get("storage_profile", {}).get("image_reference", {})
            sku = image_reference.get('sku')
            offer = image_reference.get('offer')
            publisher = image_reference.get('publisher', '')
            version = image_reference.get('exact_version') or image_reference.get('version', '')
            vm['image_publisher'] = publisher
            vm['image_offer'] = offer or ''
            vm['image_sku'] = sku or ''
            vm['image_version'] = version
            vm['image_reference_id'] = (
                f"{publisher}:{offer}:{sku}:{version}" if publisher and offer and sku else None
            )
            vm['os_version'] = sku
            vm['os'] = 'unknown'

            if offer:
                lower_offer = offer.lower()
                for op_system in OPERATING_SYSTEMS:
                    if op_system in lower_offer:
                        vm['os'] = op_system
                        break

            if vm['os'] == 'unknown' and sku:
                lower_sku = sku.lower()
                for op_system in OPERATING_SYSTEMS:
                    if op_system in lower_sku:
                        vm['os'] = op_system
                        break

            if regions is None:
                vm_data.append(vm)
            else:
                if vm.get('location') in regions or vm.get('location') == 'global':
                    vm_data.append(vm)
        return vm_data

    except HttpResponseError as e:
        logger.warning(f"Error while retrieving virtual machines - {e}")
        return []


def load_vms(neo4j_session: neo4j.Session, subscription_id: str, vm_list: List[Dict], update_tag: int) -> None:
    ingest_vm = """
    UNWIND $vms AS vm
    MERGE (v:AzureVirtualMachine{id: vm.id})
    ON CREATE SET v.firstseen = timestamp(),
    v.type = vm.type, v.location = vm.location,
    v.region = vm.location,
    v.consolelink = vm.consolelink,
    v.resourcegroup = vm.resource_group
    SET v:VirtualMachine
    SET v.lastupdated = $update_tag, v.name = vm.name,
    v.vm_id = vm.vm_id,
    v.plan = vm.plan.product, v.size = vm.hardware_profile.vm_size,
    v.license_type=vm.license_type, v.computer_name=vm.os_profile.computer_name,
    v.identity_type=vm.identity.type, v.zones=vm.zones,
    v.ultra_ssd_enabled=vm.additional_capabilities.ultra_ssd_enabled,
    v.priority=vm.priority, v.eviction_policy=vm.eviction_policy,
    v.is_spot_instance=vm.is_spot_instance,
    v.vm_size=vm.hardware_profile.vm_size,
    v.publisher=vm.storage_profile.image_reference.publisher,
    v.offer=vm.storage_profile.image_reference.offer,
    v.sku=vm.storage_profile.image_reference.sku,
    v.version=vm.storage_profile.image_reference.version,
    v.exact_version=vm.storage_profile.image_reference.exact_version,
    v.os_type=vm.os_type,
    v.os_disk_name=vm.os_disk_name,
    v.vm_os=vm.os,
    v.os_version=vm.os_version,
    v.aks_cluster_name = vm.aks_cluster_name,
    v.aks_pool_name = vm.aks_pool_name,
    v.aks_cluster_rg = vm.aks_cluster_rg
    WITH vm, v
    MATCH (owner:AzureSubscription{id: $SUBSCRIPTION_ID})
    MERGE (owner)-[r:RESOURCE]->(v)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    """

    neo4j_session.run(
        ingest_vm,
        vms=vm_list,
        SUBSCRIPTION_ID=subscription_id,
        update_tag=update_tag,
    )

    for vm in vm_list:
        load_vm_os_disk(neo4j_session, vm['id'], vm['storage_profile']['os_disk'], update_tag)
        if vm.get('storage_profile', {}).get('data_disks'):
            load_vm_data_disks(neo4j_session, vm['id'], vm['storage_profile']['data_disks'], update_tag)

        if vm.get('network_security_group', []) != []:
            load_vm_security_groups_relationship(neo4j_session, vm['id'], vm.get('network_security_group'), update_tag)

        if vm.get('network_interfaces', []) != []:
            load_vm_network_interfaces_relationship(neo4j_session, vm['id'], vm.get('network_interfaces'), update_tag)
        if vm.get("user_assigned_identities"):
            load_vm_managed_identities(neo4j_session, vm['id'], vm.get("user_assigned_identities"), update_tag)
        resource_group = get_azure_resource_group_name(vm.get('id'))
        _attach_vm_resource_group(neo4j_session, vm['id'], resource_group, update_tag)
        _attach_vm_properties_public_ip(neo4j_session, vm['id'], update_tag)
        _attach_vm_properties_private_ip(neo4j_session, vm['id'], update_tag)

    load_vm_image_relations(neo4j_session, vm_list, update_tag)


def load_vm_image_relations(neo4j_session: neo4j.Session, vm_list: List[Dict], update_tag: int) -> None:
    ingest_vm_image = """
    UNWIND $vms AS vm
    WITH vm
    WHERE vm.image_reference_id IS NOT NULL
    MERGE (img:AzureImage {id: vm.image_reference_id})
    ON CREATE SET img.firstseen = timestamp()
    SET img.lastupdated = $update_tag,
        img.publisher = vm.image_publisher,
        img.offer = vm.image_offer,
        img.sku = vm.image_sku,
        img.version = vm.image_version
    WITH img, vm
    MATCH (v:AzureVirtualMachine {id: vm.id})
    MERGE (v)-[:HAS]->(img)
    MERGE (v)-[rel:HAS]->(img)
    ON CREATE SET rel.firstseen = timestamp()
    SET rel.lastupdated = $update_tag
    """
    neo4j_session.run(
        ingest_vm_image,
        vms=vm_list,
        update_tag=update_tag,
    )


def _attach_vm_properties_public_ip(tx: neo4j.Transaction, vm_id: str, update_tag) -> None:
    ingest_vm_properties = """
    MATCH (vm:AzureVirtualMachine{id: $vm_id})-[:MEMBER_NETWORK_INTERFACE]->(:AzureNetworkInterface)-[:MEMBER_PUBLIC_IP_ADDRESS]->(ip:AzurePublicIPAddress)
    SET vm.public_ip=ip.ipAddress,
    vm.is_static_ip=ip.isStaticIp,
    vm.lastupdated= $update_tag
    """
    tx.run(
        ingest_vm_properties,
        vm_id=vm_id,
        update_tag=update_tag,
    )


def _attach_vm_properties_private_ip(tx: neo4j.Transaction, vm_id: str, update_tag) -> None:
    ingest_vm_properties = """
    MATCH (vm:AzureVirtualMachine{id: $vm_id})-[:MEMBER_NETWORK_INTERFACE]->(:AzureNetworkInterface)-[:CONTAINS]->(ip:AzureNetworkInterfaceIPConfiguration)
    SET vm.private_ip=ip.private_ip_address,
    vm.lastupdated = $update_tag
    """
    tx.run(
        ingest_vm_properties,
        vm_id=vm_id,
        update_tag=update_tag,
    )


def _load_vm_security_groups_relationship(tx: neo4j.Transaction, vm_id: str, data_list: List[Dict], update_tag: int) -> None:  # noqa: E501
    ingest_vm_sg = """
    UNWIND $sg_list AS sg
    MATCH (sg:AzureNetworkSecurityGroup{id: sg.id})
    WITH sg
    MATCH (v:AzureVirtualMachine{id: $vm_id})
    MERGE (v)-[r:MEMBER_NETWORK_SECURITY_GROUP]->(sg)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    """

    tx.run(
        ingest_vm_sg,
        sg_list=data_list,
        vm_id=vm_id,
        update_tag=update_tag,
    )


def _load_vm_network_interfaces_relationship(tx: neo4j.Transaction, vm_id: str, data_list: List[Dict], update_tag: int) -> None:  # noqa: E501
    ingest_vm_ni = """
    UNWIND $ni_list AS ni
    MATCH (n:AzureNetworkInterface{id: ni.id})
    WITH n
    MATCH (v:AzureVirtualMachine{id: $vm_id})
    MERGE (v)-[r:MEMBER_NETWORK_INTERFACE]->(n)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    """
    tx.run(
        ingest_vm_ni,
        ni_list=data_list,
        vm_id=vm_id,
        update_tag=update_tag,
    )


def _attach_vm_resource_group(tx: neo4j.Transaction, vm_id: str, resource_group: str, update_tag: int) -> None:
    ingest_vm = """
    match (vm:AzureVirtualMachine{id: $vm_id})
    with vm
    MATCH (res:AzureResourceGroup{name: $resource_group})
    MERGE (vm)-[r:RESOURCE_GROUP]->(res)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    """
    tx.run(
        ingest_vm,
        resource_group=resource_group,
        vm_id=vm_id,
        update_tag=update_tag,
    )


def get_vm_extensions_list(vm_list: List[Dict], client: ComputeManagementClient, common_job_parameters: Dict) -> List[Dict]:  # noqa: E501
    try:
        vm_extensions_list: List[Dict] = []
        for vm in vm_list:
            exts = client.virtual_machine_extensions.list(resource_group_name=vm['resource_group'], vm_name=vm['name'])

            if len(exts.value) > 0:
                vm_extensions_list.extend(exts.value)

        exts = []
        for extension in vm_extensions_list:
            exts.append({
                'id': extension.id,
                'resource_group': get_azure_resource_group_name(extension.id),
                'vm_id': extension.id[:extension.id.index("/extensions")],
                'consolelink': azure_console_link.get_console_link(id=vm['id'], primary_ad_domain_name=common_job_parameters['Azure_Primary_AD_Domain_Name']),  # noqa: E501
                'type': extension.type,
                'name': extension.name,
                'location': extension.location,
            })

        return exts

    except HttpResponseError as e:
        logger.warning(f"Error while retrieving virtual machine extensions- {e}")
        return []


def _load_vm_extensions_tx(tx: neo4j.Transaction, vm_extensions_list: List[Dict], update_tag: int) -> None:
    ingest_vm_extension = """
    UNWIND $vm_extensions_list AS extension
    MERGE (v:AzureVirtualMachineExtension{id: extension.id})
    ON CREATE SET v.firstseen = timestamp(), v.location = extension.location,
    v.consolelink = extension.consolelink,
    v.region = extension.location
    SET v.lastupdated = $update_tag, v.name = extension.name,
    v.type = extension.type
    WITH v,extension
    MATCH (owner:AzureVirtualMachine{id: extension.vm_id})
    MERGE (owner)-[r:CONTAIN]->(v)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    """

    tx.run(
        ingest_vm_extension,
        vm_extensions_list=vm_extensions_list,
        update_tag=update_tag,
    )
    for vm_extension in vm_extensions_list:
        resource_group = get_azure_resource_group_name(vm_extension.get('id'))
        _attach_resource_group_vm_extensions(tx, vm_extension['id'], resource_group, update_tag)


def _attach_resource_group_vm_extensions(tx: neo4j.Transaction, vm_extension_id: str, resource_group: str, update_tag: int) -> None:  # noqa: E501
    ingest_resource_group = """
    MATCH (v:AzureVirtualMachineExtension{id: $vm_extension_id})
    WITH v
    MATCH(rg:AzureResourceGroup{name: $resource_group})
        MERGE (v)-[res:RESOURCE_GROUP]->(rg)
        ON CREATE SET res.firstseen = timestamp()
        SET res.lastupdated = $update_tag
    """
    tx.run(
        ingest_resource_group,
        vm_extension_id=vm_extension_id,
        resource_group=resource_group,
        update_tag=update_tag,
    )


def cleanup_virtual_machine_extensions(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('azure_import_virtual_machines_extensions_cleanup.json', neo4j_session, common_job_parameters)


def sync_virtual_machine_extensions(
    neo4j_session: neo4j.Session, client: ComputeManagementClient, vm_list: List[Dict], update_tag: int,
    common_job_parameters: Dict,
) -> None:
    vm_extensions_list = get_vm_extensions_list(vm_list, client, common_job_parameters)
    load_vm_extensions(neo4j_session, vm_extensions_list, update_tag)
    cleanup_virtual_machine_extensions(neo4j_session, common_job_parameters)


def get_vm_available_sizes_list(vm_list: List[Dict], client: ComputeManagementClient) -> List[Dict]:
    try:
        vm_available_sizes_list: List[Dict] = []
        for vm in vm_list:
            vm_available_size_list = list(
                map(
                    lambda x: x.as_dict(), client.virtual_machines.list_available_sizes(
                        resource_group_name=vm['resource_group'], vm_name=vm['name'],
                    ),
                ),
            )

            for size in vm_available_size_list:
                size['resource_group'] = vm['resource_group']
                size['vm_id'] = vm['id']
                size['id'] = f"{vm['id']}/Size/{size['name']}"
                size["location"] = vm.get("location", "global")
            vm_available_sizes_list = vm_available_sizes_list + vm_available_size_list

        return vm_available_sizes_list

    except HttpResponseError as e:
        logger.warning(f"Error while retrieving virtual machine available_sizes - {e}")
        return []


def _load_vm_available_sizes_tx(tx: neo4j.Transaction, vm_available_sizes_list: List[Dict], update_tag: int) -> None:
    ingest_vm_size = """
    UNWIND $vm_available_sizes_list AS size
    MERGE (v:AzureVirtualMachineAvailableSize{id: size.id})
    ON CREATE SET v.firstseen = timestamp(), v.numberOfCores = size.numberOfCores,
    v.location= size.location,v.region= size.location
    SET v.lastupdated = $update_tag, v.osDiskSizeInMB = size.osDiskSizeInMB,
    v.name = size.name,
    v.resourceDiskSizeInMB = size.resourceDiskSizeInMB,
    v.memoryInMB=size.memoryInMB,
    v.maxDataDiskCount=size.maxDataDiskCount
    WITH v,size
    MATCH (owner:AzureVirtualMachine{id: size.vm_id})
    MERGE (owner)-[r:CONTAIN]->(v)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    """

    tx.run(
        ingest_vm_size,
        vm_available_sizes_list=vm_available_sizes_list,
        update_tag=update_tag,
    )
    for vm_available_size in vm_available_sizes_list:
        resource_group = get_azure_resource_group_name(vm_available_size.get('id'))
        _attach_resource_group_vm_available_size(tx, vm_available_size['id'], resource_group, update_tag)


def _attach_resource_group_vm_available_size(tx: neo4j.Transaction, vm_available_size_id: str, resource_group: str, update_tag: int) -> None:  # noqa: E501
    ingest_vm_size = """
    MATCH (v:AzureVirtualMachineAvailableSize{id: $size_id})
    WITH v
    MATCH (rg:AzureResourceGroup{name: $resource_group})
    MERGE (v)-[r:RESOURCE_GROUP]->(rg)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    """

    tx.run(
        ingest_vm_size,
        size_id=vm_available_size_id,
        resource_group=resource_group,
        update_tag=update_tag,
    )


def cleanup_virtual_machine_available_sizes(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job(
        'azure_import_virtual_machines_vm_available_sizes_list_cleanup.json',
        neo4j_session, common_job_parameters,
    )


def sync_virtual_machine_available_sizes(
    neo4j_session: neo4j.Session, client: ComputeManagementClient, vm_list: List[Dict], update_tag: int,
    common_job_parameters: Dict,
) -> None:
    vm_available_sizes_list = get_vm_available_sizes_list(vm_list, client)
    load_vm_available_sizes(neo4j_session, vm_available_sizes_list, update_tag)
    cleanup_virtual_machine_available_sizes(neo4j_session, common_job_parameters)


def get_vm_scale_sets_list(credentials: Credentials, subscription_id: str, regions: list, common_job_parameters: Dict) -> List[Dict]:  # noqa: E501
    try:
        client = get_client(credentials, subscription_id)
        vm_scale_sets_list = list(map(lambda x: x.as_dict(), client.virtual_machine_scale_sets.list_all()))
        sets_list = []
        for set in vm_scale_sets_list:
            x = set['id'].split('/')
            set['resource_group'] = x[x.index('resourceGroups') + 1]
            set['consolelink'] = azure_console_link.get_console_link(
                id=set['id'], primary_ad_domain_name=common_job_parameters['Azure_Primary_AD_Domain_Name'],
            )
            aks_tags = _extract_aks_tags(set.get('tags', {}))
            set['aks_cluster_name'] = aks_tags['aks_cluster_name']
            set['aks_pool_name'] = aks_tags['aks_pool_name']
            set['aks_cluster_rg'] = aks_tags['aks_cluster_rg']
            if regions is None:
                sets_list.append(set)
            else:
                if set.get('location') in regions or set.get('location') == 'global':
                    sets_list.append(set)
        return sets_list

    except HttpResponseError as e:
        logger.warning(f"Error while retrieving virtual machines scale_sets_list - {e}")
        return []


def _load_vm_scale_sets_tx(
    tx: neo4j.Transaction, subscription_id: str, vm_scale_sets_list: List[Dict], update_tag: int,
) -> None:
    ingest_scale_set = """
    UNWIND $vm_scale_sets_list AS set
    MERGE (a:AzureVirtualMachineScaleSet{id: set.id})
    ON CREATE SET a.firstseen = timestamp(),
    a.type = set.type,
    a.location = set.location,
    a.region = set.location,
    a.consolelinke = set.consolelink,
    a.resourcegroup = set.resource_group
    SET a:AzureVMScaleSet
    SET a.lastupdated = $update_tag,
    a.name = set.name,
    a.aks_cluster_name = set.aks_cluster_name,
    a.aks_pool_name = set.aks_pool_name,
    a.aks_cluster_rg = set.aks_cluster_rg,
    a.subscription_id = $SUBSCRIPTION_ID,
    a.name = set.name
    WITH a
    MATCH (owner:AzureSubscription{id: $SUBSCRIPTION_ID})
    MERGE (owner)-[r:RESOURCE]->(a)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    """

    tx.run(
        ingest_scale_set,
        vm_scale_sets_list=vm_scale_sets_list,
        SUBSCRIPTION_ID=subscription_id,
        update_tag=update_tag,
    )
    for vm_scale_set in vm_scale_sets_list:
        resource_group = get_azure_resource_group_name(vm_scale_set.get('id'))
        _attach_resource_group_vm_scale_sets(tx, vm_scale_set['id'], resource_group, update_tag)


def _attach_resource_group_vm_scale_sets(tx: neo4j.Transaction, vm_scale_set_id: str, resource_group: str, update_tag: int) -> None:  # noqa: E501
    ingest_resource_group = """
        MATCH (a:AzureVirtualMachineScaleSet{id: $set_id})
        with a
        MATCH(rg:AzureResourceGroup{name:$resource_group})
        MERGE (a)-[res:RESOURCE_GROUP]->(rg)
        ON CREATE SET res.firstseen = timestamp()
        SET res.lastupdated = $update_tag
        """
    tx.run(
        ingest_resource_group,
        set_id=vm_scale_set_id,
        resource_group=resource_group,
        update_tag=update_tag,
    )


def cleanup_vm_scale_sets(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('azure_import_virtual_machines_scale_sets_cleanup.json', neo4j_session, common_job_parameters)


def sync_vm_scale_sets(
    neo4j_session: neo4j.Session, credentials: Credentials, subscription_id: str, update_tag: int,
    common_job_parameters: Dict, regions: list,
) -> None:
    client = get_client(credentials, subscription_id)
    vm_scale_sets_list = get_vm_scale_sets_list(credentials, subscription_id, regions, common_job_parameters)

    load_vm_scale_sets(neo4j_session, subscription_id, vm_scale_sets_list, update_tag)
    vmss.sync_vm_scale_sets_vms_part_of_relationships(
        neo4j_session,
        client,
        vm_scale_sets_list,
        update_tag,
        subscription_id,
    )
    cleanup_vm_scale_sets(neo4j_session, common_job_parameters)
    sync_virtual_machine_scale_sets_extensions(
        neo4j_session, client, vm_scale_sets_list, update_tag, common_job_parameters,
    )


def get_vm_scale_sets_extensions_list(vm_scale_sets_list: List[Dict], client: ComputeManagementClient, common_job_parameters: Dict) -> List[Dict]:  # noqa: E501
    try:
        vm_scale_sets_extensions_list: List[Dict] = []
        for set in vm_scale_sets_list:
            extensions_list = list(
                map(
                    lambda x: x.as_dict(), client.virtual_machine_scale_set_extensions.list(
                        resource_group_name=set['resource_group'], vm_scale_set_name=set['name'],
                    ),
                ),
            )
            for extension in extensions_list:
                extension["location"] = set.get("location", "global")
                x = extension['id'].split('/')
                extension['resource_group'] = x[x.index('resourceGroups') + 1]
                extension['set_id'] = extension['id'][:extension['id'].index("/extensions")]
                extension['consolelink'] = azure_console_link.get_console_link(
                    id=extension['id'], primary_ad_domain_name=common_job_parameters['Azure_Primary_AD_Domain_Name'],
                )

            vm_scale_sets_extensions_list.extend(extensions_list)

        return vm_scale_sets_extensions_list

    except HttpResponseError as e:
        logger.warning(f"Error while retrieving virtual machine scale set extensions- {e}")
        return []


def _load_vm_scale_sets_extensions_tx(
    tx: neo4j.Transaction, vm_scale_sets_extensions_list: List[Dict], update_tag: int,
) -> None:
    ingest_vm_scale_sets_extension = """
    UNWIND $vm_scale_sets_extensions_list AS extension
    MERGE (v:AzureVirtualMachineScaleSetExtension{id: extension.id})
    ON CREATE SET v.firstseen = timestamp()
    SET v.lastupdated = $update_tag, v.name = extension.name,
    v.location = extension.location,
    v.region = extension.location,
    v.consolelink = extension.consolelink,
    v.type = extension.type
    WITH v,extension
    MATCH (owner:AzureVirtualMachineScaleSet{id: extension.set_id})
    MERGE (owner)-[r:CONTAIN]->(v)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    """

    tx.run(
        ingest_vm_scale_sets_extension,
        vm_scale_sets_extensions_list=vm_scale_sets_extensions_list,
        update_tag=update_tag,
    )
    for vm_scale_sets_extension in vm_scale_sets_extensions_list:
        resource_group = get_azure_resource_group_name(vm_scale_sets_extension.get('id'))
        _attach_resource_group_vm_scale_sets_extension(tx, vm_scale_sets_extension['id'], resource_group, update_tag)


def _attach_resource_group_vm_scale_sets_extension(tx: neo4j.Transaction, vm_scale_sets_extension_id: str, resource_group: str, update_tag: int) -> None:  # noqa: E501
    ingest_vm_scale_sets_extension_resource_group = """
    MATCH (v:AzureVirtualMachineScaleSetExtension{id: $extension_id})
    WITH v
    MATCH(rg:AzureResourceGroup{name: $resource_group})
        MERGE (v)-[res:RESOURCE_GROUP]->(rg)
        ON CREATE SET res.firstseen = timestamp()
        SET res.lastupdated = $update_tag
    """
    tx.run(
        ingest_vm_scale_sets_extension_resource_group,
        extension_id=vm_scale_sets_extension_id,
        resource_group=resource_group,
        update_tag=update_tag,

    )


def cleanup_virtual_machine_scale_sets_extensions(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job(
        'azure_import_virtual_machines_scale_sets_extensions_cleanup.json',
        neo4j_session, common_job_parameters,
    )


def sync_virtual_machine_scale_sets_extensions(
    neo4j_session: neo4j.Session, client: ComputeManagementClient, vm_list: List[Dict], update_tag: int,
    common_job_parameters: Dict,
) -> None:
    vm_scale_sets_extensions_list = get_vm_scale_sets_extensions_list(vm_list, client, common_job_parameters)
    load_vm_scale_sets_extensions(neo4j_session, vm_scale_sets_extensions_list, update_tag)
    cleanup_virtual_machine_scale_sets_extensions(neo4j_session, common_job_parameters)


def load_vm_data_disks(neo4j_session: neo4j.Session, vm_id: str, data_disks: List[Dict], update_tag: int) -> None:
    ingest_data_disk = """
    UNWIND $disks AS disk
    MERGE (d:AzureDisk:AzureDataDisk{id: disk.managed_disk.id})
    ON CREATE SET d.firstseen = timestamp(), d.lun = disk.lun
    SET d.lastupdated = $update_tag, d.name = disk.name,
    d.vhd = disk.vhd.uri, d.image = disk.image.uri,
    d.location = disk.location,
    d.region = disk.location,
    d.size = disk.disk_size_gb, d.caching = disk.caching,
    d.createoption = disk.create_option, d.write_accelerator_enabled=disk.write_accelerator_enabled,
    d.managed_disk_storage_type=disk.managed_disk.storage_account_type, d.disk_type = 'datadisk'
    WITH d
    MATCH (owner:AzureVirtualMachine{id: $VM_ID})
    MERGE (owner)-[r:ATTACHED_TO]->(d)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    """

    # for disk in data_disks:
    neo4j_session.run(
        ingest_data_disk,
        disks=data_disks,
        VM_ID=vm_id,
        update_tag=update_tag,
    )


def load_vm_managed_identities(neo4j_session: neo4j.Session, vm_id: str, managed_identities: List[str], update_tag: int) -> None:  # noqa: E501
    ingest_managed_identity = """
    UNWIND $managed_identities AS ua
    MERGE (i:AzureManagedIdentity{id: toLower(ua)})
    ON CREATE SET i:AzurePrincipal,
    i.firstseen = timestamp()
    SET i.lastupdated = $update_tag
    WITH i
    MATCH (v:AzureVirtualMachine{id: $VM_ID})
    MERGE (v)-[rel:HAS]->(i)
    ON CREATE SET rel.firstseen = timestamp()
    SET rel.lastupdated = $update_tag
    """

    neo4j_session.run(
        ingest_managed_identity,
        managed_identities=managed_identities,
        VM_ID=vm_id,
        update_tag=update_tag,
    )


def load_vm_os_disk(neo4j_session: neo4j.Session, vm_id: str, os_disk: Dict, update_tag: int) -> None:
    ingest_os_disk = """
    MERGE (d:AzureDisk{id: $disk.managed_disk.id})
    ON CREATE SET d.firstseen = timestamp()
    SET d.lastupdated = $update_tag, d.name = $disk.name,
    d.vhd = $disk.vhd.uri, d.image = $disk.image.uri,
    d.size = $disk.disk_size_gb, d.caching = $disk.caching,
    d.createoption = $disk.create_option, d.write_accelerator_enabled=$disk.write_accelerator_enabled,
    d.managed_disk_storage_type=$disk.managed_disk.storage_account_type, d.disk_type = 'osdisk'
    WITH d
    MATCH (owner:AzureVirtualMachine{id: $VM_ID})
    MERGE (owner)-[r:ATTACHED_TO]->(d)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    """

    neo4j_session.run(
        ingest_os_disk,
        disk=os_disk,
        VM_ID=vm_id,
        update_tag=update_tag,
    )


def _attach_snapshot_disk(neo4j_session: neo4j.Session, snapshot_id: str, disk_id: str, update_tag: int):
    attach_snapshot_disk = """
    MATCH (s:AzureSnapshot{id: $snapshot_id})
    WITH s
    MATCH (d:AzureDisk{id: $disk_id})
    WITH s, d
    MERGE (d)-[r:HAS]->(s)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    """
    neo4j_session.run(
        attach_snapshot_disk,
        snapshot_id=snapshot_id,
        disk_id=disk_id,
        update_tag=update_tag,
    )


def cleanup_virtual_machine(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('azure_import_virtual_machines_cleanup.json', neo4j_session, common_job_parameters)


def get_disks(credentials: Credentials, subscription_id: str, regions: list, common_job_parameters: Dict) -> List[Dict]:
    try:
        client = get_client(credentials, subscription_id)
        disk_list = list(map(lambda x: x.as_dict(), client.disks.list()))
        disk_data = []
        for disk in disk_list:
            x = disk['id'].split('/')
            disk['resource_group'] = x[x.index('resourceGroups') + 1]
            disk['consolelink'] = azure_console_link.get_console_link(
                id=disk['id'], primary_ad_domain_name=common_job_parameters['Azure_Primary_AD_Domain_Name'],
            )
            if regions is None:
                disk_data.append(disk)
            else:
                if disk.get('location') in regions or disk.get('location') == 'global':
                    disk_data.append(disk)
        return disk_data

    except HttpResponseError as e:
        logger.warning(f"Error while retrieving disks - {e}")
        return []


def load_disks(neo4j_session: neo4j.Session, subscription_id: str, disk_list: List[Dict], update_tag: int) -> None:
    ingest_disks = """
    UNWIND $disks AS disk
    MERGE (d:AzureDisk{id: disk.id})
    ON CREATE SET d.firstseen = timestamp(),
    d.type = disk.type, d.location = disk.location,
    d.region = disk.location,
    d.consolelink = disk.consolelink,
    d.resourcegroup = disk.resource_group
    SET d.lastupdated = $update_tag, d.name = disk.name,
    d.createoption = disk.creation_data.create_option, d.disksizegb = disk.disk_size_gb,
    d.encryption = disk.encryption_settings_collection.enabled, d.maxshares = disk.max_shares,
    d.network_access_policy = disk.network_access_policy,
    d.ostype = disk.os_type, d.tier = disk.tier,
    d.sku = disk.sku.name, d.zones = disk.zones
    WITH d
    MATCH (owner:AzureSubscription{id: $SUBSCRIPTION_ID})
    MERGE (owner)-[r:RESOURCE]->(d)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag"""

    neo4j_session.run(
        ingest_disks,
        disks=disk_list,
        SUBSCRIPTION_ID=subscription_id,
        update_tag=update_tag,
    )
    for disk in disk_list:
        resource_group = get_azure_resource_group_name(disk.get('id'))
        _attach_resource_group_disk(neo4j_session, disk['id'], resource_group, update_tag)


def _attach_resource_group_disk(neo4j_session: neo4j.Session, disk_id: str, resource_group: str, update_tag: int) -> None:  # noqa: E501
    ingest_disks = """
    MATCH (d:AzureDisk{id: $disk_id})
    WITH d
    MATCH (rg:AzureResourceGroup{name: $resource_group})
    MERGE (d)-[r:RESOURCE_GROUP]->(rg)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    """
    neo4j_session.run(
        ingest_disks,
        disk_id=disk_id,
        resource_group=resource_group,
        update_tag=update_tag,
    )


def cleanup_disks(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('azure_import_disks_cleanup.json', neo4j_session, common_job_parameters)


def get_snapshots_list(credentials: Credentials, subscription_id: str, regions: list, common_job_parameters: Dict) -> List[Dict]:  # noqa: E501
    try:
        client = get_client(credentials, subscription_id)
        snapshots = list(map(lambda x: x.as_dict(), client.snapshots.list()))
        snapshot_list = []
        for snapshot in snapshots:
            x = snapshot['id'].split('/')
            snapshot['resource_group'] = x[x.index('resourceGroups') + 1]
            snapshot['consolelink'] = azure_console_link.get_console_link(
                id=snapshot['id'], primary_ad_domain_name=common_job_parameters['Azure_Primary_AD_Domain_Name'],
            )
            if regions is None:
                snapshot_list.append(snapshot)
            else:
                if snapshot.get('location') in regions or snapshot.get('location') == 'global':
                    snapshot_list.append(snapshot)
        return snapshot_list

    except HttpResponseError as e:
        logger.warning(f"Error while retrieving snapshots - {e}")
        return []


def load_snapshots(neo4j_session: neo4j.Session, subscription_id: str, snapshots: List[Dict], update_tag: int) -> None:
    ingest_snapshots = """
    UNWIND $snapshots as snapshot
    MERGE (s:AzureSnapshot{id: snapshot.id})
    ON CREATE SET s.firstseen = timestamp(),
    s.resourcegroup = snapshot.resource_group,
    s.type = snapshot.type, s.location = snapshot.location,
    s.consolelink = snapshot.consolelink,
    s.region = snapshot.location
    SET s.lastupdated = $update_tag, s.name = snapshot.name, s.time_created = snapshot.time_created,
    s.createoption = snapshot.creation_data.create_option, s.disksizegb = snapshot.disk_size_gb,
    s.encryption = snapshot.encryption_settings_collection.enabled, s.incremental = snapshot.incremental,
    s.network_access_policy = snapshot.network_access_policy, s.ostype = snapshot.os_type,
    s.tier = snapshot.tier, s.sku = snapshot.sku.name, s.disk_access_id = snapshot.disk_access_id
    WITH s
    MATCH (owner:AzureSubscription{id: $SUBSCRIPTION_ID})
    MERGE (owner)-[r:RESOURCE]->(s)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag"""

    neo4j_session.run(
        ingest_snapshots,
        snapshots=snapshots,
        SUBSCRIPTION_ID=subscription_id,
        update_tag=update_tag,
    )
    for snapshot in snapshots:
        resource_group = get_azure_resource_group_name(snapshot.get('id'))
        _attach_resource_group_disk_snapshot(neo4j_session, snapshot['id'], resource_group, update_tag)


def _attach_resource_group_disk_snapshot(neo4j_session: neo4j.Session, snapshot_id: str, resource_group: str, update_tag: int) -> None:  # noqa: E501
    ingest_snapshots = """
    MATCH (s:AzureSnapshot{id: $snapshot_id})
    WITH s
    MATCH (rg:AzureResourceGroup{name: $resource_group})
    MERGE (s)-[r:RESOURCE_GROUP]->(rg)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    """
    neo4j_session.run(
        ingest_snapshots,
        snapshot_id=snapshot_id,
        resource_group=resource_group,
        update_tag=update_tag,
    )


def cleanup_snapshot(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('azure_import_snapshots_cleanup.json', neo4j_session, common_job_parameters)


def sync_virtual_machine(
    neo4j_session: neo4j.Session, credentials: Credentials, subscription_id: str, update_tag: int,
    common_job_parameters: Dict, regions: list,
) -> None:
    # client = get_client(credentials, subscription_id)
    vm_list = get_vm_list(credentials, subscription_id, regions, common_job_parameters)

    load_vms(neo4j_session, subscription_id, vm_list, update_tag)
    # sync_virtual_machine_extensions(neo4j_session, client, vm_list, update_tag, common_job_parameters)
    # sync_virtual_machine_available_sizes(neo4j_session, client, vm_list, update_tag, common_job_parameters)

    cleanup_virtual_machine(neo4j_session, common_job_parameters)


def sync_disk(
    neo4j_session: neo4j.Session, credentials: Credentials, subscription_id: str, update_tag: int,
    common_job_parameters: Dict, regions: list,
) -> None:
    disk_list = get_disks(credentials, subscription_id, regions, common_job_parameters)

    load_disks(neo4j_session, subscription_id, disk_list, update_tag)
    cleanup_disks(neo4j_session, common_job_parameters)


def sync_snapshot(
    neo4j_session: neo4j.Session, credentials: Credentials, subscription_id: str, update_tag: int,
    common_job_parameters: Dict, regions: list,
) -> None:
    snapshots = get_snapshots_list(credentials, subscription_id, regions, common_job_parameters)

    load_snapshots(neo4j_session, subscription_id, snapshots, update_tag)
    for snapshot in snapshots:
        if snapshot.get("creation_data").get("create_option", "") == "Copy":
            _attach_snapshot_disk(
                neo4j_session, snapshot["id"],
                snapshot["creation_data"]["source_resource_id"], update_tag,
            )

    cleanup_snapshot(neo4j_session, common_job_parameters)


@timeit
def link_compute_to_aks(neo4j_session: neo4j.Session, update_tag: int) -> None:
    """Links Azure VMs and VM Scale Sets to AKS Clusters and Node Pools based on tags."""

    # 1. Link VM Scale Sets and VMs to the AKS Cluster
    cluster_query = """
    MATCH (node) WHERE node:AzureVirtualMachine OR node:AzureVirtualMachineScaleSet
    WITH node WHERE node.aks_cluster_name IS NOT NULL AND node.aks_cluster_rg IS NOT NULL
    MATCH (c:AzureCluster {name: node.aks_cluster_name, resourcegroup: node.aks_cluster_rg})
    MERGE (c)-[r:HAS_NODE]->(node)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    """

    # 2. Link VM Scale Sets and VMs to the AKS Node Pool (Agent Pool)
    pool_query = """
    MATCH (node) WHERE node:AzureVirtualMachine OR node:AzureVirtualMachineScaleSet
    WITH node WHERE node.aks_cluster_name IS NOT NULL AND node.aks_pool_name IS NOT NULL AND node.aks_cluster_rg IS NOT NULL
    MATCH (c:AzureCluster {name: node.aks_cluster_name, resourcegroup: node.aks_cluster_rg})-[:HAS]->(p:AzureClusterAgentPool {name: node.aks_pool_name})
    MERGE (p)-[r:HAS_NODE]->(node)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    """

    neo4j_session.run(cluster_query, update_tag=update_tag)
    neo4j_session.run(pool_query, update_tag=update_tag)


@timeit
def cleanup_aks_compute_links(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    """Removes stale HAS_NODE relationships between AKS resources and Compute resources."""
    run_cleanup_job('azure_aks_compute_links_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync(
    neo4j_session: neo4j.Session, credentials: Credentials, subscription_id: str, update_tag: int,
    common_job_parameters: Dict, regions: list,
) -> None:
    logger.info("Syncing VM for subscription '%s'.", subscription_id)

    sync_virtual_machine(neo4j_session, credentials, subscription_id, update_tag, common_job_parameters, regions)
    sync_vm_scale_sets(neo4j_session, credentials, subscription_id, update_tag, common_job_parameters, regions)
    sync_disk(neo4j_session, credentials, subscription_id, update_tag, common_job_parameters, regions)
    sync_snapshot(neo4j_session, credentials, subscription_id, update_tag, common_job_parameters, regions)
    link_compute_to_aks(neo4j_session, update_tag)
    cleanup_aks_compute_links(neo4j_session, common_job_parameters)
