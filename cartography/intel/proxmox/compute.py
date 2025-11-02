"""
Sync Proxmox VMs and LXC containers.

Follows Cartography's Get → Transform → Load pattern.
"""

import logging
from typing import Any, Dict, List

from cartography.client.core.tx import run_write_query
from cartography.util import timeit

logger = logging.getLogger(__name__)


# ============================================================================
# GET functions
# ============================================================================

@timeit
def get_vms_for_node(proxmox_client, node_name: str) -> List[Dict[str, Any]]:
    """
    Get all QEMU VMs on a node.

    :param proxmox_client: Proxmox API client
    :param node_name: Node name
    :return: List of VM dicts
    """
    try:
        vms = proxmox_client.nodes(node_name).qemu.get()
        for vm in vms:
            vm['type'] = 'qemu'
            vm['node'] = node_name
        return vms
    except Exception as e:
        logger.warning(f"Could not get VMs for node {node_name}: {e}")
        return []


@timeit
def get_containers_for_node(proxmox_client, node_name: str) -> List[Dict[str, Any]]:
    """
    Get all LXC containers on a node.

    :param proxmox_client: Proxmox API client
    :param node_name: Node name
    :return: List of container dicts
    """
    try:
        containers = proxmox_client.nodes(node_name).lxc.get()
        for ct in containers:
            ct['type'] = 'lxc'
            ct['node'] = node_name
        return containers
    except Exception as e:
        logger.warning(f"Could not get containers for node {node_name}: {e}")
        return []


@timeit
def get_vm_config(proxmox_client, node_name: str, vmid: int, vm_type: str) -> Dict[str, Any]:
    """
    Get detailed configuration for a VM or container.

    :param proxmox_client: Proxmox API client
    :param node_name: Node name
    :param vmid: VM ID
    :param vm_type: 'qemu' or 'lxc'
    :return: VM configuration dict
    """
    try:
        if vm_type == 'qemu':
            return proxmox_client.nodes(node_name).qemu(vmid).config.get()
        else:
            return proxmox_client.nodes(node_name).lxc(vmid).config.get()
    except Exception as e:
        logger.warning(f"Could not get config for {vm_type} {vmid} on {node_name}: {e}")
        return {}


# ============================================================================
# TRANSFORM functions
# ============================================================================

def transform_vm_data(vms: List[Dict[str, Any]], cluster_id: str) -> List[Dict[str, Any]]:
    """
    Transform VM and container data into standard format.

    :param vms: Raw VM data from API (both qemu and lxc)
    :param cluster_id: Parent cluster ID
    :return: List of transformed VM dicts
    """
    transformed_vms = []

    for vm in vms:
        vm_id = f"{vm['node']}:{vm['vmid']}"

        # Parse tags if they exist
        tags = []
        if vm.get('tags'):
            tags = [t.strip() for t in vm.get('tags', '').split(';') if t.strip()]

        transformed_vms.append({
            'id': vm_id,
            'vmid': vm['vmid'],
            'name': vm.get('name', ''),
            'node': vm['node'],
            'cluster_id': cluster_id,
            'type': vm['type'],
            'status': vm.get('status'),
            'template': vm.get('template', False),
            'cpu_cores': vm.get('cpus') or vm.get('cores', 0),
            'cpu_sockets': vm.get('sockets', 1),
            'memory': vm.get('maxmem', 0),
            'disk_size': vm.get('maxdisk', 0),
            'uptime': vm.get('uptime', 0),
            'tags': tags,
        })

    return transformed_vms


def extract_disk_data(vm_config: Dict[str, Any], vmid: int) -> List[Dict[str, Any]]:
    """
    Extract disk configurations from VM config.

    :param vm_config: VM configuration dict
    :param vmid: VM ID
    :return: List of disk dicts
    """
    disks = []

    # QEMU disks: scsi0, virtio0, sata0, ide0, etc.
    # LXC disks: rootfs, mp0, mp1, etc.
    for key, value in vm_config.items():
        if key.startswith(('scsi', 'virtio', 'sata', 'ide', 'rootfs', 'mp')):
            if isinstance(value, str):
                # Parse disk string: "storage:vmid/vm-vmid-disk-0.qcow2,size=32G"
                parts = value.split(',')
                disk_path = parts[0]

                disk_data = {
                    'id': f"{vmid}:{key}",
                    'disk_id': key,
                    'vmid': vmid,
                }

                if ':' in disk_path:
                    disk_data['storage'] = disk_path.split(':')[0]

                # Parse parameters
                for part in parts[1:]:
                    if '=' in part:
                        param_key, param_value = part.split('=', 1)
                        if param_key == 'size':
                            # Convert size to bytes
                            size_str = param_value.upper()
                            if size_str.endswith('G'):
                                disk_data['size'] = int(float(size_str[:-1]) * 1024**3)
                            elif size_str.endswith('M'):
                                disk_data['size'] = int(float(size_str[:-1]) * 1024**2)
                            elif size_str.endswith('T'):
                                disk_data['size'] = int(float(size_str[:-1]) * 1024**4)
                        elif param_key == 'backup':
                            disk_data['backup'] = param_value == '1'
                        elif param_key == 'cache':
                            disk_data['cache'] = param_value

                disks.append(disk_data)

    return disks


def extract_network_data(vm_config: Dict[str, Any], vmid: int) -> List[Dict[str, Any]]:
    """
    Extract network interface configurations from VM config.

    :param vm_config: VM configuration dict
    :param vmid: VM ID
    :return: List of network interface dicts
    """
    interfaces = []

    # QEMU: net0, net1, etc.
    # LXC: net0, net1, etc.
    for key, value in vm_config.items():
        if key.startswith('net') and len(key) > 3 and key[3:].isdigit():
            if isinstance(value, str):
                # Parse network string: "virtio=XX:XX:XX:XX:XX:XX,bridge=vmbr0,firewall=1"
                nic_data = {
                    'id': f"{vmid}:{key}",
                    'net_id': key,
                    'vmid': vmid,
                }

                parts = value.split(',')
                for part in parts:
                    if '=' in part:
                        param_key, param_value = part.split('=', 1)
                        if param_key in ('virtio', 'e1000', 'rtl8139', 'vmxnet3'):
                            nic_data['model'] = param_key
                            nic_data['mac_address'] = param_value
                        elif param_key == 'bridge':
                            nic_data['bridge'] = param_value
                        elif param_key == 'firewall':
                            nic_data['firewall'] = param_value == '1'
                        elif param_key == 'tag':
                            try:
                                nic_data['vlan_tag'] = int(param_value)
                            except ValueError:
                                pass

                interfaces.append(nic_data)

    return interfaces


# ============================================================================
# LOAD functions
# ============================================================================

def load_vms(neo4j_session, vms: List[Dict[str, Any]], update_tag: int) -> None:
    """
    Load VM data into Neo4j and create relationships.

    :param neo4j_session: Neo4j session
    :param vms: List of transformed VM dicts
    :param update_tag: Sync timestamp
    """
    query = """
    UNWIND $VMs as vm_data
    MERGE (v:ProxmoxVM{id: vm_data.id})
    ON CREATE SET v.firstseen = timestamp()
    SET v.vmid = vm_data.vmid,
        v.name = vm_data.name,
        v.node = vm_data.node,
        v.cluster_id = vm_data.cluster_id,
        v.type = vm_data.type,
        v.status = vm_data.status,
        v.template = vm_data.template,
        v.cpu_cores = vm_data.cpu_cores,
        v.cpu_sockets = vm_data.cpu_sockets,
        v.memory = vm_data.memory,
        v.disk_size = vm_data.disk_size,
        v.uptime = vm_data.uptime,
        v.tags = vm_data.tags,
        v.lastupdated = $UpdateTag
    WITH v, vm_data
    MATCH (n:ProxmoxNode{id: vm_data.node})
    MERGE (n)-[r:HOSTS_VM]->(v)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $UpdateTag
    """

    run_write_query(
        neo4j_session,
        query,
        VMs=vms,
        UpdateTag=update_tag,
    )


def load_disks(neo4j_session, disks: List[Dict[str, Any]], update_tag: int) -> None:
    """
    Load disk data into Neo4j and create relationships.

    :param neo4j_session: Neo4j session
    :param disks: List of disk dicts
    :param update_tag: Sync timestamp
    """
    if not disks:
        return

    query = """
    UNWIND $Disks as disk_data
    MERGE (d:ProxmoxDisk{id: disk_data.id})
    ON CREATE SET d.firstseen = timestamp()
    SET d.disk_id = disk_data.disk_id,
        d.vmid = disk_data.vmid,
        d.storage = disk_data.storage,
        d.size = disk_data.size,
        d.backup = disk_data.backup,
        d.cache = disk_data.cache,
        d.lastupdated = $UpdateTag
    WITH d, disk_data
    MATCH (v:ProxmoxVM) WHERE v.vmid = disk_data.vmid
    MERGE (v)-[r:HAS_DISK]->(d)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $UpdateTag
    WITH d, disk_data
    OPTIONAL MATCH (s:ProxmoxStorage{id: disk_data.storage})
    FOREACH (storage IN CASE WHEN s IS NOT NULL THEN [s] ELSE [] END |
        MERGE (d)-[r2:STORED_ON]->(storage)
        ON CREATE SET r2.firstseen = timestamp()
        SET r2.lastupdated = $UpdateTag
    )
    """

    run_write_query(
        neo4j_session,
        query,
        Disks=disks,
        UpdateTag=update_tag,
    )


def load_network_interfaces(neo4j_session, interfaces: List[Dict[str, Any]], update_tag: int) -> None:
    """
    Load network interface data into Neo4j and create relationships.

    :param neo4j_session: Neo4j session
    :param interfaces: List of network interface dicts
    :param update_tag: Sync timestamp
    """
    if not interfaces:
        return

    query = """
    UNWIND $Interfaces as if_data
    MERGE (i:ProxmoxNetworkInterface{id: if_data.id})
    ON CREATE SET i.firstseen = timestamp()
    SET i.net_id = if_data.net_id,
        i.vmid = if_data.vmid,
        i.bridge = if_data.bridge,
        i.mac_address = if_data.mac_address,
        i.model = if_data.model,
        i.firewall = if_data.firewall,
        i.vlan_tag = if_data.vlan_tag,
        i.lastupdated = $UpdateTag
    WITH i, if_data
    MATCH (v:ProxmoxVM) WHERE v.vmid = if_data.vmid
    MERGE (v)-[r:HAS_NETWORK_INTERFACE]->(i)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $UpdateTag
    """

    run_write_query(
        neo4j_session,
        query,
        Interfaces=interfaces,
        UpdateTag=update_tag,
    )


# ============================================================================
# SYNC function
# ============================================================================

@timeit
def sync(
    neo4j_session,
    proxmox_client,
    cluster_id: str,
    update_tag: int,
    common_job_parameters: Dict[str, Any],
) -> None:
    """
    Sync VM and container compute resources.

    :param neo4j_session: Neo4j session
    :param proxmox_client: Proxmox API client
    :param cluster_id: Parent cluster ID
    :param update_tag: Sync timestamp
    :param common_job_parameters: Common parameters
    """
    logger.info("Syncing Proxmox VMs and containers")

    # Get all nodes to iterate
    nodes = proxmox_client.nodes.get()

    all_vms = []
    all_disks = []
    all_interfaces = []

    for node in nodes:
        node_name = node['node']

        # Get VMs and containers
        vms = get_vms_for_node(proxmox_client, node_name)
        containers = get_containers_for_node(proxmox_client, node_name)

        combined_vms = vms + containers
        all_vms.extend(combined_vms)

        # Get detailed config for each VM
        for vm in combined_vms:
            vm_config = get_vm_config(proxmox_client, node_name, vm['vmid'], vm['type'])

            # Extract disks and network interfaces
            disks = extract_disk_data(vm_config, vm['vmid'])
            interfaces = extract_network_data(vm_config, vm['vmid'])

            all_disks.extend(disks)
            all_interfaces.extend(interfaces)

    # Transform and load
    transformed_vms = transform_vm_data(all_vms, cluster_id)
    load_vms(neo4j_session, transformed_vms, update_tag)

    if all_disks:
        load_disks(neo4j_session, all_disks, update_tag)

    if all_interfaces:
        load_network_interfaces(neo4j_session, all_interfaces, update_tag)

    logger.info(
        f"Synced {len(transformed_vms)} VMs/containers with "
        f"{len(all_disks)} disks and {len(all_interfaces)} network interfaces",
    )
