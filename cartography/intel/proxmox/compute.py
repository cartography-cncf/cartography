"""
Sync Proxmox VMs and LXC containers.

Follows Cartography's Get → Transform → Load pattern.
"""

import logging
from typing import Any
from typing import Dict
from typing import List
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import neo4j

from cartography.client.core.tx import load
from cartography.models.proxmox.compute import ProxmoxDiskSchema
from cartography.models.proxmox.compute import ProxmoxNetworkInterfaceSchema
from cartography.models.proxmox.compute import ProxmoxVMSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


# ============================================================================
# GET functions
# ============================================================================


@timeit
def get_vms_for_node(proxmox_client: Any, node_name: str) -> List[Dict[str, Any]]:
    """
    Get all QEMU VMs on a node.

    :param proxmox_client: Proxmox API client
    :param node_name: Node name
    :return: List of VM dicts
    """
    try:
        vms = proxmox_client.nodes(node_name).qemu.get()
        for vm in vms:
            vm["type"] = "qemu"
            vm["node"] = node_name
        return vms
    except Exception as e:
        logger.warning(f"Could not get VMs for node {node_name}: {e}")
        return []


@timeit
def get_containers_for_node(
    proxmox_client: Any, node_name: str
) -> List[Dict[str, Any]]:
    """
    Get all LXC containers on a node.

    :param proxmox_client: Proxmox API client
    :param node_name: Node name
    :return: List of container dicts
    """
    try:
        containers = proxmox_client.nodes(node_name).lxc.get()
        for ct in containers:
            ct["type"] = "lxc"
            ct["node"] = node_name
        return containers
    except Exception as e:
        logger.warning(f"Could not get containers for node {node_name}: {e}")
        return []


@timeit
def get_vm_config(
    proxmox_client: Any, node_name: str, vmid: int, vm_type: str
) -> Dict[str, Any]:
    """
    Get detailed configuration for a VM or container.

    :param proxmox_client: Proxmox API client
    :param node_name: Node name
    :param vmid: VM ID
    :param vm_type: 'qemu' or 'lxc'
    :return: VM configuration dict
    """
    try:
        if vm_type == "qemu":
            return proxmox_client.nodes(node_name).qemu(vmid).config.get()
        else:
            return proxmox_client.nodes(node_name).lxc(vmid).config.get()
    except Exception as e:
        logger.warning(f"Could not get config for {vm_type} {vmid} on {node_name}: {e}")
        return {}


@timeit
def get_guest_agent_info(
    proxmox_client: Any, node_name: str, vmid: int
) -> Dict[str, Any]:
    """
    Get guest agent information for a VM.

    Requires QEMU Guest Agent installed and running in the VM.
    Returns empty dict if agent not available or any error occurs.

    :param proxmox_client: Proxmox API client
    :param node_name: Node name
    :param vmid: VM ID
    :return: Guest agent data dict
    """
    guest_data: Dict[str, Any] = {}

    try:
        # Get OS information
        os_info = proxmox_client.nodes(node_name).qemu(vmid).agent("get-osinfo").get()
        if os_info and "result" in os_info:
            result = os_info["result"]
            guest_data["guest_os_name"] = result.get("name") or result.get("id")
            guest_data["guest_os_version"] = result.get("version") or result.get(
                "version-id"
            )
            guest_data["guest_kernel_release"] = result.get("kernel-release")
            guest_data["guest_kernel_version"] = result.get("kernel-version")
            guest_data["guest_machine"] = result.get("machine")
    except Exception as e:
        logger.debug(f"Could not get OS info via guest agent for VM {vmid}: {e}")

    try:
        # Get hostname
        hostname_info = (
            proxmox_client.nodes(node_name).qemu(vmid).agent("get-host-name").get()
        )
        if hostname_info and "result" in hostname_info:
            guest_data["guest_hostname"] = hostname_info["result"].get("host-name")
    except Exception as e:
        logger.debug(f"Could not get hostname via guest agent for VM {vmid}: {e}")

    try:
        # Get network interfaces with actual IPs
        network_info = (
            proxmox_client.nodes(node_name)
            .qemu(vmid)
            .agent("network-get-interfaces")
            .get()
        )
        if network_info and "result" in network_info:
            # Store raw network interface data for later processing
            guest_data["guest_network_interfaces"] = network_info["result"]
    except Exception as e:
        logger.debug(
            f"Could not get network interfaces via guest agent for VM {vmid}: {e}"
        )

    # Mark agent as enabled if we got any data
    guest_data["agent_enabled"] = bool(guest_data)

    return guest_data


# ============================================================================
# TRANSFORM functions
# ============================================================================


def transform_vm_data(
    vms: List[Dict[str, Any]], cluster_id: str
) -> List[Dict[str, Any]]:
    """
    Transform VM and container data into standard format.

    :param vms: Raw VM data from API (both qemu and lxc)
    :param cluster_id: Parent cluster ID
    :return: List of transformed VM dicts
    """
    transformed_vms = []

    for vm in vms:
        vm_id = f"{vm['node']}/{vm['type']}/{vm['vmid']}"

        # Parse tags if they exist
        tags = []
        if vm.get("tags"):
            tags = [t.strip() for t in vm.get("tags", "").split(";") if t.strip()]

        # Calculate vCPUs (cores * sockets)
        cores = vm.get("cores", 0)
        sockets = vm.get("sockets", 1)
        vcpus = cores * sockets if cores else 0

        transformed_vms.append(
            {
                "id": vm_id,
                "vmid": vm["vmid"],
                "name": vm.get("name", ""),
                "node": vm["node"],
                "cluster_id": cluster_id,
                "type": vm["type"],
                "status": vm.get("status"),
                "template": vm.get("template", False),
                "cpu_cores": vm.get("cpus") or vm.get("cores", 0),
                "cpu_sockets": vm.get("sockets", 1),
                "cores": cores,
                "sockets": sockets,
                "vcpus": vcpus,
                "memory": vm.get("maxmem", 0),
                "disk_size": vm.get("maxdisk", 0),
                "uptime": vm.get("uptime", 0),
                "tags": tags,
                # Store config fields that will be enriched later
                # These are set to None initially and populated during config fetch
                "ostype": vm.get("ostype"),
                "onboot": vm.get("onboot"),
                "protection": vm.get("protection"),
                "description": vm.get("description"),
                "vmgenid": vm.get("vmgenid"),
                "machine": vm.get("machine"),
                "bios": vm.get("bios"),
                "boot": vm.get("boot"),
                "scsihw": vm.get("scsihw"),
                "cpu": vm.get("cpu"),
                "cpulimit": vm.get("cpulimit"),
                "cpuunits": vm.get("cpuunits"),
                "hotplug": vm.get("hotplug"),
                "lock": vm.get("lock"),
                # Memory configuration
                "balloon": vm.get("balloon"),
                "shares": vm.get("shares"),
                # Advanced CPU/Hardware configuration
                "numa": vm.get("numa"),
                "kvm": vm.get("kvm"),
                "localtime": vm.get("localtime"),
                "keyboard": vm.get("keyboard"),
                "vga": vm.get("vga"),
                "agent_config": vm.get("agent_config"),
                "args": vm.get("args"),
                "hugepages": vm.get("hugepages"),
                "keephugepages": vm.get("keephugepages"),
                "freeze": vm.get("freeze"),
                "watchdog": vm.get("watchdog"),
                "rng0": vm.get("rng0"),
                "audio0": vm.get("audio0"),
                "efidisk0": vm.get("efidisk0"),
                "tpmstate0": vm.get("tpmstate0"),
                "hostpci_count": vm.get("hostpci_count", 0),
                "usb_count": vm.get("usb_count", 0),
                "serial_count": vm.get("serial_count", 0),
                "parallel_count": vm.get("parallel_count", 0),
                # Guest agent fields (populated if guest agent enabled)
                "guest_hostname": vm.get("guest_hostname"),
                "guest_os_name": vm.get("guest_os_name"),
                "guest_os_version": vm.get("guest_os_version"),
                "guest_kernel_release": vm.get("guest_kernel_release"),
                "guest_kernel_version": vm.get("guest_kernel_version"),
                "guest_machine": vm.get("guest_machine"),
                "agent_enabled": vm.get("agent_enabled", False),
            }
        )

    return transformed_vms


def extract_disk_data(vm_config: Dict[str, Any], vmid: str) -> List[Dict[str, Any]]:
    """
    Extract disk configurations from VM config.

    :param vm_config: VM configuration dict
    :param vmid: Full VM ID (node/type/vmid format, e.g. "node1/qemu/100")
    :return: List of disk dicts
    """
    disks = []

    # QEMU disks: scsi0, virtio0, sata0, ide0, efidisk0, tpmstate0, etc.
    # LXC disks: rootfs, mp0, mp1, etc.
    for key, value in vm_config.items():
        # Check if this is a valid disk key
        is_disk = False

        # rootfs is always a valid LXC disk
        if key == "rootfs":
            is_disk = True
        # mp followed by digits (e.g., mp0, mp1) are LXC mount points
        elif key.startswith("mp") and len(key) > 2 and key[2:].isdigit():
            is_disk = True
        # QEMU disk types must have numeric suffix (e.g., scsi0, not scsihw)
        elif key.startswith(("scsi", "virtio", "sata", "ide", "efidisk", "tpmstate")):
            # Find where the prefix ends
            for prefix in ("scsi", "virtio", "sata", "ide", "efidisk", "tpmstate"):
                if key.startswith(prefix):
                    suffix = key[len(prefix) :]
                    # Check if suffix is a digit
                    if suffix and suffix.isdigit():
                        is_disk = True
                    break

        if is_disk and isinstance(value, str):
            # Parse disk string: "storage:vmid/vm-vmid-disk-0.qcow2,size=32G"
            parts = value.split(",")
            disk_path = parts[0]

            # Extract integer vmid from full VM ID (e.g., "node1/qemu/100" -> 100)
            vmid_int = int(vmid.split("/")[-1])

            disk_data = {
                "id": f"{vmid}:{key}",  # Full ID with node/type/vmid prefix
                "disk_id": key,
                "vmid": vmid_int,  # Integer vmid for matching relationships
            }

            if ":" in disk_path:
                disk_data["storage"] = disk_path.split(":")[0]

            # Parse parameters
            is_cdrom = False
            for part in parts[1:]:
                if "=" in part:
                    param_key, param_value = part.split("=", 1)
                    if param_key == "size":
                        # Convert size to bytes
                        size_str = param_value.upper()
                        if size_str.endswith("G"):
                            disk_data["size"] = int(float(size_str[:-1]) * 1024**3)
                        elif size_str.endswith("M"):
                            disk_data["size"] = int(float(size_str[:-1]) * 1024**2)
                        elif size_str.endswith("T"):
                            disk_data["size"] = int(float(size_str[:-1]) * 1024**4)
                    elif param_key == "backup":
                        disk_data["backup"] = param_value == "1"
                    elif param_key == "cache":
                        disk_data["cache"] = param_value
                    elif param_key == "format":
                        disk_data["format"] = param_value
                    elif param_key == "iothread":
                        disk_data["iothread"] = param_value == "1"
                    elif param_key == "discard":
                        disk_data["discard"] = param_value
                    elif param_key == "ssd":
                        disk_data["ssd"] = param_value == "1"
                    elif param_key == "replicate":
                        disk_data["replicate"] = param_value == "1"
                    elif param_key == "serial":
                        disk_data["serial"] = param_value
                    elif param_key == "wwn":
                        disk_data["wwn"] = param_value
                    elif param_key == "snapshot":
                        disk_data["snapshot"] = param_value == "1"
                    elif param_key == "iops":
                        try:
                            disk_data["iops"] = int(param_value)
                        except ValueError:
                            pass
                    elif param_key == "iops_rd":
                        try:
                            disk_data["iops_rd"] = int(param_value)
                        except ValueError:
                            pass
                    elif param_key == "iops_wr":
                        try:
                            disk_data["iops_wr"] = int(param_value)
                        except ValueError:
                            pass
                    elif param_key == "mbps":
                        try:
                            disk_data["mbps"] = float(param_value)
                        except ValueError:
                            pass
                    elif param_key == "mbps_rd":
                        try:
                            disk_data["mbps_rd"] = float(param_value)
                        except ValueError:
                            pass
                    elif param_key == "mbps_wr":
                        try:
                            disk_data["mbps_wr"] = float(param_value)
                        except ValueError:
                            pass
                    elif param_key == "mbps_max":
                        try:
                            disk_data["mbps_max"] = float(param_value)
                        except ValueError:
                            pass
                    elif param_key == "mbps_rd_max":
                        try:
                            disk_data["mbps_rd_max"] = float(param_value)
                        except ValueError:
                            pass
                    elif param_key == "mbps_wr_max":
                        try:
                            disk_data["mbps_wr_max"] = float(param_value)
                        except ValueError:
                            pass
                    elif param_key == "iops_max":
                        try:
                            disk_data["iops_max"] = int(param_value)
                        except ValueError:
                            pass
                    elif param_key == "iops_rd_max":
                        try:
                            disk_data["iops_rd_max"] = int(param_value)
                        except ValueError:
                            pass
                    elif param_key == "iops_wr_max":
                        try:
                            disk_data["iops_wr_max"] = int(param_value)
                        except ValueError:
                            pass
                    elif param_key == "media":
                        disk_data["media"] = param_value
                        # Skip CD-ROM mounts
                        if param_value == "cdrom":
                            is_cdrom = True
                    elif param_key == "ro":
                        disk_data["ro"] = param_value == "1"
                    elif param_key == "detect_zeroes":
                        disk_data["detect_zeroes"] = param_value

            # Only append if not a CD-ROM
            if not is_cdrom:
                disks.append(disk_data)

    return disks


def extract_network_data(vm_config: Dict[str, Any], vmid: str) -> List[Dict[str, Any]]:
    """
    Extract network interface configurations from VM config.

    :param vm_config: VM configuration dict
    :param vmid: Full VM ID (node/type/vmid format, e.g. "node1/qemu/100")
    :return: List of network interface dicts
    """
    interfaces = []

    # QEMU: net0, net1, etc.
    # LXC: net0, net1, etc.
    for key, value in vm_config.items():
        if key.startswith("net") and len(key) > 3 and key[3:].isdigit():
            if isinstance(value, str):
                # Parse network string: "virtio=XX:XX:XX:XX:XX:XX,bridge=vmbr0,firewall=1,ip=192.168.1.10/24,gw=192.168.1.1"
                # Extract integer vmid from full VM ID (e.g., "node1/qemu/100" -> 100)
                vmid_int = int(vmid.split("/")[-1])

                nic_data = {
                    "id": f"{vmid}:{key}",  # Full ID with node/type/vmid prefix
                    "net_id": key,
                    "vmid": vmid_int,  # Integer vmid for matching relationships
                }

                parts = value.split(",")
                for part in parts:
                    if "=" in part:
                        param_key, param_value = part.split("=", 1)
                        if param_key in (
                            "virtio",
                            "e1000",
                            "rtl8139",
                            "vmxnet3",
                            "veth",
                        ):
                            nic_data["model"] = param_key
                            nic_data["mac_address"] = param_value
                        elif param_key == "hwaddr":
                            # LXC containers use hwaddr instead of model=MAC
                            nic_data["mac_address"] = param_value
                        elif param_key == "name":
                            # LXC containers use name parameter
                            nic_data["model"] = "veth"  # LXC default model
                        elif param_key == "bridge":
                            nic_data["bridge"] = param_value
                        elif param_key == "firewall":
                            nic_data["firewall"] = param_value == "1"
                        elif param_key == "tag":
                            try:
                                nic_data["vlan_tag"] = int(param_value)
                            except ValueError:
                                pass
                        elif param_key == "ip":
                            nic_data["ip"] = param_value
                        elif param_key == "ip6":
                            nic_data["ip6"] = param_value
                        elif param_key == "gw":
                            nic_data["gw"] = param_value
                        elif param_key == "gw6":
                            nic_data["gw6"] = param_value
                        elif param_key == "mtu":
                            try:
                                nic_data["mtu"] = int(param_value)
                            except ValueError:
                                pass
                        elif param_key == "rate":
                            try:
                                nic_data["rate"] = float(param_value)
                            except ValueError:
                                pass
                        elif param_key == "link_down":
                            nic_data["link_up"] = (
                                param_value != "1"
                            )  # Invert link_down to link_up
                        elif param_key == "queues":
                            try:
                                nic_data["queues"] = int(param_value)
                            except ValueError:
                                pass
                        elif param_key == "trunks":
                            nic_data["trunks"] = param_value
                            # If trunks is present, 'tag' (stored as vlan_tag) represents the native VLAN
                            # Store it in both fields for compatibility
                            if "vlan_tag" in nic_data:
                                nic_data["tag"] = nic_data["vlan_tag"]

                interfaces.append(nic_data)

    return interfaces


def enrich_interfaces_with_guest_data(
    interfaces: List[Dict[str, Any]],
    guest_network_interfaces: List[Dict[str, Any]],
) -> None:
    """
    Enrich configured network interfaces with actual IP addresses from guest agent.

    Matches interfaces by MAC address and adds runtime IP information.

    :param interfaces: List of configured network interface dicts (modified in place)
    :param guest_network_interfaces: Guest agent network interface data
    """
    if not guest_network_interfaces:
        return

    # Build a map of MAC address to guest interface data
    guest_ifaces_by_mac: Dict[str, Dict[str, Any]] = {}
    for guest_iface in guest_network_interfaces:
        mac = guest_iface.get("hardware-address", "").lower()
        if mac:
            guest_ifaces_by_mac[mac] = guest_iface

    # Enrich configured interfaces with guest data
    for iface in interfaces:
        config_mac = iface.get("mac_address", "").lower()
        if config_mac in guest_ifaces_by_mac:
            guest_iface = guest_ifaces_by_mac[config_mac]

            # Extract IP addresses
            ip_addresses = guest_iface.get("ip-addresses", [])
            ipv4_addrs = []
            ipv6_addrs = []

            for ip_info in ip_addresses:
                ip_addr = ip_info.get("ip-address")
                prefix = ip_info.get("prefix")
                ip_type = ip_info.get("ip-address-type", "").lower()

                if ip_addr and prefix is not None:
                    cidr = f"{ip_addr}/{prefix}"
                    if ip_type == "ipv4":
                        ipv4_addrs.append(cidr)
                    elif ip_type == "ipv6":
                        ipv6_addrs.append(cidr)

            # Store actual runtime IPs (multiple IPs possible)
            if ipv4_addrs:
                iface["actual_ipv4"] = ",".join(ipv4_addrs)
            if ipv6_addrs:
                iface["actual_ipv6"] = ",".join(ipv6_addrs)

            # Store interface name from guest
            guest_name = guest_iface.get("name")
            if guest_name:
                iface["guest_interface_name"] = guest_name


# ============================================================================
# LOAD functions - using modern data model
# ============================================================================


def load_vms(
    neo4j_session: "neo4j.Session",
    vms: List[Dict[str, Any]],
    cluster_id: str,
    update_tag: int,
) -> None:
    """
    Load VM data into Neo4j using modern data model.

    :param neo4j_session: Neo4j session
    :param vms: List of transformed VM dicts
    :param cluster_id: Parent cluster ID
    :param update_tag: Sync timestamp
    """
    load(
        neo4j_session,
        ProxmoxVMSchema(),
        vms,
        lastupdated=update_tag,
        CLUSTER_ID=cluster_id,
    )


def load_disks(
    neo4j_session: "neo4j.Session",
    disks: List[Dict[str, Any]],
    cluster_id: str,
    update_tag: int,
) -> None:
    """
    Load disk data into Neo4j using modern data model.

    :param neo4j_session: Neo4j session
    :param disks: List of disk dicts
    :param cluster_id: Parent cluster ID
    :param update_tag: Sync timestamp
    """
    if not disks:
        return

    load(
        neo4j_session,
        ProxmoxDiskSchema(),
        disks,
        lastupdated=update_tag,
        CLUSTER_ID=cluster_id,
    )


def load_network_interfaces(
    neo4j_session: "neo4j.Session",
    interfaces: List[Dict[str, Any]],
    cluster_id: str,
    update_tag: int,
) -> None:
    """
    Load network interface data into Neo4j using modern data model.

    :param neo4j_session: Neo4j session
    :param interfaces: List of network interface dicts
    :param cluster_id: Parent cluster ID
    :param update_tag: Sync timestamp
    """
    if not interfaces:
        return

    load(
        neo4j_session,
        ProxmoxNetworkInterfaceSchema(),
        interfaces,
        lastupdated=update_tag,
        CLUSTER_ID=cluster_id,
    )


# ============================================================================
# SYNC function
# ============================================================================


@timeit
def sync(
    neo4j_session: "neo4j.Session",
    proxmox_client: Any,
    cluster_id: str,
    update_tag: int,
    common_job_parameters: Dict[str, Any],
    enable_guest_agent: bool = False,
) -> None:
    """
    Sync VM and container compute resources.

    :param neo4j_session: Neo4j session
    :param proxmox_client: Proxmox API client
    :param cluster_id: Parent cluster ID
    :param update_tag: Sync timestamp
    :param common_job_parameters: Common parameters
    :param enable_guest_agent: Enable QEMU guest agent data collection
    """
    logger.info("Syncing Proxmox VMs and containers")

    # Get all nodes to iterate
    nodes = proxmox_client.nodes.get()

    all_vms = []
    all_disks = []
    all_interfaces = []

    for node in nodes:
        node_name = node["node"]

        # Get VMs and containers
        vms = get_vms_for_node(proxmox_client, node_name)
        containers = get_containers_for_node(proxmox_client, node_name)

        combined_vms = vms + containers
        all_vms.extend(combined_vms)

        # Get detailed config for each VM
        for vm in combined_vms:
            vm_config = get_vm_config(proxmox_client, node_name, vm["vmid"], vm["type"])

            # Merge config data into VM record
            # These fields are available in the detailed config but not in the list API
            vm.update(
                {
                    "cores": vm_config.get("cores"),
                    "sockets": vm_config.get("sockets", 1),
                    "ostype": vm_config.get("ostype"),
                    "onboot": vm_config.get("onboot"),
                    "protection": vm_config.get("protection"),
                    "description": vm_config.get("description"),
                    "vmgenid": vm_config.get("vmgenid"),
                    "machine": vm_config.get("machine"),
                    "bios": vm_config.get("bios"),
                    "boot": vm_config.get("boot"),
                    "scsihw": vm_config.get("scsihw"),
                    "cpu": vm_config.get("cpu"),
                    "cpulimit": vm_config.get("cpulimit"),
                    "cpuunits": vm_config.get("cpuunits"),
                    "hotplug": vm_config.get("hotplug"),
                    "lock": vm_config.get("lock"),
                    "balloon": vm_config.get("balloon"),
                    "shares": vm_config.get("shares"),
                    "numa": vm_config.get("numa"),
                    "kvm": vm_config.get("kvm"),
                    "localtime": vm_config.get("localtime"),
                    "keyboard": vm_config.get("keyboard"),
                    "vga": vm_config.get("vga"),
                    "agent_config": vm_config.get("agent"),
                    "args": vm_config.get("args"),
                    "hugepages": vm_config.get("hugepages"),
                    "keephugepages": vm_config.get("keephugepages"),
                    "freeze": vm_config.get("freeze"),
                    "watchdog": vm_config.get("watchdog"),
                    "rng0": vm_config.get("rng0"),
                    "audio0": vm_config.get("audio0"),
                    "efidisk0": vm_config.get("efidisk0"),
                    "tpmstate0": vm_config.get("tpmstate0"),
                }
            )

            # Count device arrays (hostpci0-9, usb0-9, serial0-3, parallel0-2)
            vm["hostpci_count"] = sum(
                1 for k in vm_config.keys() if k.startswith("hostpci")
            )
            vm["usb_count"] = sum(1 for k in vm_config.keys() if k.startswith("usb"))
            vm["serial_count"] = sum(
                1 for k in vm_config.keys() if k.startswith("serial")
            )
            vm["parallel_count"] = sum(
                1 for k in vm_config.keys() if k.startswith("parallel")
            )

            # Extract disks and network interfaces
            # Build full VM ID for child resources (node/type/vmid format)
            full_vm_id = f"{vm['node']}/{vm['type']}/{vm['vmid']}"
            disks = extract_disk_data(vm_config, full_vm_id)
            interfaces = extract_network_data(vm_config, full_vm_id)

            # Get guest agent data if enabled and VM is QEMU
            if enable_guest_agent and vm["type"] == "qemu":
                guest_data = get_guest_agent_info(proxmox_client, node_name, vm["vmid"])
                vm.update(guest_data)

                # Enrich network interfaces with actual IPs from guest agent
                guest_network_interfaces = guest_data.get(
                    "guest_network_interfaces", []
                )
                if guest_network_interfaces:
                    enrich_interfaces_with_guest_data(
                        interfaces, guest_network_interfaces
                    )
            else:
                # Explicitly set guest agent fields to None when disabled to clear any previous values
                vm.update(
                    {
                        "guest_hostname": None,
                        "guest_os_name": None,
                        "guest_os_version": None,
                        "guest_kernel_release": None,
                        "guest_kernel_version": None,
                        "guest_machine": None,
                        "agent_enabled": False,
                    }
                )

            all_disks.extend(disks)
            all_interfaces.extend(interfaces)

    # Transform and load
    transformed_vms = transform_vm_data(all_vms, cluster_id)
    load_vms(neo4j_session, transformed_vms, cluster_id, update_tag)

    if all_disks:
        load_disks(neo4j_session, all_disks, cluster_id, update_tag)

    if all_interfaces:
        load_network_interfaces(neo4j_session, all_interfaces, cluster_id, update_tag)

    guest_agent_msg = " (guest agent enabled)" if enable_guest_agent else ""
    logger.info(
        f"Synced {len(transformed_vms)} VMs/containers{guest_agent_msg} with "
        f"{len(all_disks)} disks and {len(all_interfaces)} network interfaces",
    )
