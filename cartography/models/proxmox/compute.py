"""
Data models for Proxmox compute resources (VMs, containers, disks, network interfaces).

Follows Cartography's modern data model pattern.
"""

from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher

# ============================================================================
# ProxmoxVM Node Schema
# ============================================================================


@dataclass(frozen=True)
class ProxmoxVMNodeProperties(CartographyNodeProperties):
    """
    Properties for a ProxmoxVM node.

    Represents both QEMU VMs and LXC containers.
    """

    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    vmid: PropertyRef = PropertyRef("vmid", extra_index=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    node: PropertyRef = PropertyRef("node")
    cluster_id: PropertyRef = PropertyRef("cluster_id")
    type: PropertyRef = PropertyRef("type")  # 'qemu' or 'lxc'
    status: PropertyRef = PropertyRef("status")
    template: PropertyRef = PropertyRef("template")
    cpu_cores: PropertyRef = PropertyRef("cpu_cores")
    cpu_sockets: PropertyRef = PropertyRef("cpu_sockets")
    # CPU configuration from VM config (cores/sockets are from detailed config)
    cores: PropertyRef = PropertyRef("cores")  # CPU cores from config
    sockets: PropertyRef = PropertyRef("sockets")  # CPU sockets from config
    vcpus: PropertyRef = PropertyRef("vcpus")  # Total vCPUs (cores * sockets)
    memory: PropertyRef = PropertyRef("memory")
    disk_size: PropertyRef = PropertyRef("disk_size")
    uptime: PropertyRef = PropertyRef("uptime")
    tags: PropertyRef = PropertyRef("tags")
    # Additional VM configuration
    ostype: PropertyRef = PropertyRef("ostype")  # OS type (l24, l26, win10, etc.)
    onboot: PropertyRef = PropertyRef("onboot")  # Auto-start on boot
    protection: PropertyRef = PropertyRef("protection")  # Protection from deletion
    description: PropertyRef = PropertyRef("description")  # VM description
    vmgenid: PropertyRef = PropertyRef("vmgenid")  # VM generation ID
    machine: PropertyRef = PropertyRef("machine")  # QEMU machine type
    bios: PropertyRef = PropertyRef("bios")  # BIOS type (seabios/ovmf)
    boot: PropertyRef = PropertyRef("boot")  # Boot order
    scsihw: PropertyRef = PropertyRef("scsihw")  # SCSI controller type
    cpu: PropertyRef = PropertyRef("cpu")  # CPU model and flags
    cpulimit: PropertyRef = PropertyRef("cpulimit")  # CPU usage limit
    cpuunits: PropertyRef = PropertyRef("cpuunits")  # CPU weight/priority
    hotplug: PropertyRef = PropertyRef("hotplug")  # Hotplug features
    lock: PropertyRef = PropertyRef("lock")  # Lock status
    # Memory configuration
    balloon: PropertyRef = PropertyRef("balloon")  # Memory ballooning value
    shares: PropertyRef = PropertyRef("shares")  # Memory shares for ballooning
    # Advanced CPU/Hardware configuration
    numa: PropertyRef = PropertyRef("numa")  # NUMA enabled
    kvm: PropertyRef = PropertyRef("kvm")  # KVM hardware virtualization
    localtime: PropertyRef = PropertyRef("localtime")  # Use local time for RTC
    keyboard: PropertyRef = PropertyRef("keyboard")  # Keyboard layout
    vga: PropertyRef = PropertyRef("vga")  # VGA configuration
    agent_config: PropertyRef = PropertyRef("agent_config")  # Guest agent config string
    args: PropertyRef = PropertyRef("args")  # Extra QEMU arguments
    # Memory and performance features
    hugepages: PropertyRef = PropertyRef("hugepages")  # Hugepages size
    keephugepages: PropertyRef = PropertyRef(
        "keephugepages"
    )  # Keep hugepages after shutdown
    freeze: PropertyRef = PropertyRef("freeze")  # Freeze CPU at startup
    # Hardware devices
    watchdog: PropertyRef = PropertyRef("watchdog")  # Virtual watchdog device
    rng0: PropertyRef = PropertyRef("rng0")  # Random number generator
    audio0: PropertyRef = PropertyRef("audio0")  # Audio device
    efidisk0: PropertyRef = PropertyRef("efidisk0")  # EFI disk configuration
    tpmstate0: PropertyRef = PropertyRef("tpmstate0")  # TPM state disk
    # Device counts (for arrays like hostpci, usb, serial, parallel)
    hostpci_count: PropertyRef = PropertyRef(
        "hostpci_count"
    )  # Number of PCI passthrough devices
    usb_count: PropertyRef = PropertyRef("usb_count")  # Number of USB devices
    serial_count: PropertyRef = PropertyRef("serial_count")  # Number of serial ports
    parallel_count: PropertyRef = PropertyRef(
        "parallel_count"
    )  # Number of parallel ports
    # Guest agent data (optional, requires QEMU guest agent)
    guest_hostname: PropertyRef = PropertyRef("guest_hostname")  # Actual OS hostname
    guest_os_name: PropertyRef = PropertyRef("guest_os_name")  # OS name
    guest_os_version: PropertyRef = PropertyRef("guest_os_version")  # OS version
    guest_kernel_release: PropertyRef = PropertyRef(
        "guest_kernel_release"
    )  # Kernel release
    guest_kernel_version: PropertyRef = PropertyRef(
        "guest_kernel_version"
    )  # Kernel version
    guest_machine: PropertyRef = PropertyRef("guest_machine")  # Hardware arch
    agent_enabled: PropertyRef = PropertyRef("agent_enabled")  # Guest agent status


@dataclass(frozen=True)
class ProxmoxVMToClusterRelProperties(CartographyRelProperties):
    """
    Properties for relationship from ProxmoxVM to ProxmoxCluster.
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ProxmoxVMToClusterRel(CartographyRelSchema):
    """
    Relationship: (:ProxmoxVM)-[:RESOURCE]->(:ProxmoxCluster)

    Per AGENTS.md: sub_resource_relationship should point to tenant-like object.
    """

    target_node_label: str = "ProxmoxCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("CLUSTER_ID", set_in_kwargs=True),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "RESOURCE"
    properties: ProxmoxVMToClusterRelProperties = ProxmoxVMToClusterRelProperties()


@dataclass(frozen=True)
class ProxmoxVMToNodeRelProperties(CartographyRelProperties):
    """
    Properties for relationship from ProxmoxNode to ProxmoxVM.
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ProxmoxVMToNodeRel(CartographyRelSchema):
    """
    Relationship: (:ProxmoxNode)-[:HOSTS_VM]->(:ProxmoxVM)

    This is an "other_relationship" showing which node hosts the VM.
    """

    target_node_label: str = "ProxmoxNode"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("node"),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HOSTS_VM"
    properties: ProxmoxVMToNodeRelProperties = ProxmoxVMToNodeRelProperties()


@dataclass(frozen=True)
class ProxmoxVMSchema(CartographyNodeSchema):
    """
    Schema for a ProxmoxVM.

    VMs belong to clusters and are hosted on nodes.
    """

    label: str = "ProxmoxVM"
    properties: ProxmoxVMNodeProperties = ProxmoxVMNodeProperties()
    sub_resource_relationship: ProxmoxVMToClusterRel = ProxmoxVMToClusterRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            ProxmoxVMToNodeRel(),
        ]
    )


# ============================================================================
# ProxmoxDisk Node Schema
# ============================================================================


@dataclass(frozen=True)
class ProxmoxDiskNodeProperties(CartographyNodeProperties):
    """
    Properties for a ProxmoxDisk node.
    """

    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    disk_id: PropertyRef = PropertyRef("disk_id")
    vmid: PropertyRef = PropertyRef("vmid")
    storage: PropertyRef = PropertyRef("storage")
    size: PropertyRef = PropertyRef("size")
    backup: PropertyRef = PropertyRef("backup")
    cache: PropertyRef = PropertyRef("cache")
    # Additional disk configuration
    format: PropertyRef = PropertyRef("format")  # Disk format (qcow2, raw, vmdk)
    iothread: PropertyRef = PropertyRef("iothread")  # I/O thread enabled
    discard: PropertyRef = PropertyRef("discard")  # Discard/trim support
    ssd: PropertyRef = PropertyRef("ssd")  # SSD emulation flag
    replicate: PropertyRef = PropertyRef("replicate")  # Replication enabled
    serial: PropertyRef = PropertyRef("serial")  # Disk serial number
    wwn: PropertyRef = PropertyRef("wwn")  # World Wide Name
    snapshot: PropertyRef = PropertyRef("snapshot")  # Snapshot mode
    # Performance limits
    iops: PropertyRef = PropertyRef("iops")  # IOPS limit
    iops_rd: PropertyRef = PropertyRef("iops_rd")  # Read IOPS limit
    iops_wr: PropertyRef = PropertyRef("iops_wr")  # Write IOPS limit
    mbps: PropertyRef = PropertyRef("mbps")  # Bandwidth limit (MB/s)
    mbps_rd: PropertyRef = PropertyRef("mbps_rd")  # Read bandwidth limit
    mbps_wr: PropertyRef = PropertyRef("mbps_wr")  # Write bandwidth limit
    # Burst limits
    mbps_max: PropertyRef = PropertyRef("mbps_max")  # Burst bandwidth limit
    mbps_rd_max: PropertyRef = PropertyRef("mbps_rd_max")  # Burst read bandwidth
    mbps_wr_max: PropertyRef = PropertyRef("mbps_wr_max")  # Burst write bandwidth
    iops_max: PropertyRef = PropertyRef("iops_max")  # Burst IOPS limit
    iops_rd_max: PropertyRef = PropertyRef("iops_rd_max")  # Burst read IOPS
    iops_wr_max: PropertyRef = PropertyRef("iops_wr_max")  # Burst write IOPS
    # Media and access properties
    media: PropertyRef = PropertyRef("media")  # Media type (cdrom/disk)
    ro: PropertyRef = PropertyRef("ro")  # Read-only flag
    detect_zeroes: PropertyRef = PropertyRef("detect_zeroes")  # Detect zero writes


@dataclass(frozen=True)
class ProxmoxDiskToClusterRelProperties(CartographyRelProperties):
    """
    Properties for relationship from ProxmoxDisk to ProxmoxCluster.
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ProxmoxDiskToClusterRel(CartographyRelSchema):
    """
    Relationship: (:ProxmoxDisk)-[:RESOURCE]->(:ProxmoxCluster)
    """

    target_node_label: str = "ProxmoxCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("CLUSTER_ID", set_in_kwargs=True),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "RESOURCE"
    properties: ProxmoxDiskToClusterRelProperties = ProxmoxDiskToClusterRelProperties()


@dataclass(frozen=True)
class ProxmoxDiskToVMRelProperties(CartographyRelProperties):
    """
    Properties for relationship from ProxmoxVM to ProxmoxDisk.
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ProxmoxDiskToVMRel(CartographyRelSchema):
    """
    Relationship: (:ProxmoxVM)-[:HAS_DISK]->(:ProxmoxDisk)

    VMs have attached disks. Use vmid to match.
    """

    target_node_label: str = "ProxmoxVM"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "vmid": PropertyRef("vmid"),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_DISK"
    properties: ProxmoxDiskToVMRelProperties = ProxmoxDiskToVMRelProperties()


@dataclass(frozen=True)
class ProxmoxDiskToStorageRelProperties(CartographyRelProperties):
    """
    Properties for relationship from ProxmoxDisk to ProxmoxStorage.
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ProxmoxDiskToStorageRel(CartographyRelSchema):
    """
    Relationship: (:ProxmoxDisk)-[:STORED_ON]->(:ProxmoxStorage)

    Disks are stored on storage backends.
    """

    target_node_label: str = "ProxmoxStorage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("storage"),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "STORED_ON"
    properties: ProxmoxDiskToStorageRelProperties = ProxmoxDiskToStorageRelProperties()


@dataclass(frozen=True)
class ProxmoxDiskSchema(CartographyNodeSchema):
    """
    Schema for a ProxmoxDisk.

    Disks belong to VMs and are stored on storage backends.
    """

    label: str = "ProxmoxDisk"
    properties: ProxmoxDiskNodeProperties = ProxmoxDiskNodeProperties()
    sub_resource_relationship: ProxmoxDiskToClusterRel = ProxmoxDiskToClusterRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            ProxmoxDiskToVMRel(),
            ProxmoxDiskToStorageRel(),
        ]
    )


# ============================================================================
# ProxmoxNetworkInterface Node Schema
# ============================================================================


@dataclass(frozen=True)
class ProxmoxNetworkInterfaceNodeProperties(CartographyNodeProperties):
    """
    Properties for a ProxmoxNetworkInterface node.
    """

    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    net_id: PropertyRef = PropertyRef("net_id")
    vmid: PropertyRef = PropertyRef("vmid")
    bridge: PropertyRef = PropertyRef("bridge")
    mac_address: PropertyRef = PropertyRef("mac_address", extra_index=True)
    model: PropertyRef = PropertyRef("model")
    firewall: PropertyRef = PropertyRef("firewall")
    vlan_tag: PropertyRef = PropertyRef("vlan_tag")
    # Additional networking properties
    ip: PropertyRef = PropertyRef("ip")  # IPv4 address
    ip6: PropertyRef = PropertyRef("ip6")  # IPv6 address
    gw: PropertyRef = PropertyRef("gw")  # Gateway
    gw6: PropertyRef = PropertyRef("gw6")  # IPv6 gateway
    mtu: PropertyRef = PropertyRef("mtu")  # MTU size
    rate: PropertyRef = PropertyRef("rate")  # Bandwidth rate limit
    link_up: PropertyRef = PropertyRef("link_up")  # Link status
    # Advanced network configuration
    queues: PropertyRef = PropertyRef("queues")  # Multi-queue setting (VirtIO)
    trunks: PropertyRef = PropertyRef("trunks")  # VLAN trunk configuration
    tag: PropertyRef = PropertyRef("tag")  # Native VLAN tag for trunk
    # Guest agent runtime data (actual IPs from running VM)
    actual_ipv4: PropertyRef = PropertyRef("actual_ipv4")  # Actual IPv4 addresses (CSV)
    actual_ipv6: PropertyRef = PropertyRef("actual_ipv6")  # Actual IPv6 addresses (CSV)
    guest_interface_name: PropertyRef = PropertyRef(
        "guest_interface_name"
    )  # Interface name in guest OS


@dataclass(frozen=True)
class ProxmoxNetworkInterfaceToClusterRelProperties(CartographyRelProperties):
    """
    Properties for relationship from ProxmoxNetworkInterface to ProxmoxCluster.
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ProxmoxNetworkInterfaceToClusterRel(CartographyRelSchema):
    """
    Relationship: (:ProxmoxNetworkInterface)-[:RESOURCE]->(:ProxmoxCluster)
    """

    target_node_label: str = "ProxmoxCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("CLUSTER_ID", set_in_kwargs=True),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "RESOURCE"
    properties: ProxmoxNetworkInterfaceToClusterRelProperties = (
        ProxmoxNetworkInterfaceToClusterRelProperties()
    )


@dataclass(frozen=True)
class ProxmoxNetworkInterfaceToVMRelProperties(CartographyRelProperties):
    """
    Properties for relationship from ProxmoxVM to ProxmoxNetworkInterface.
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ProxmoxNetworkInterfaceToVMRel(CartographyRelSchema):
    """
    Relationship: (:ProxmoxVM)-[:HAS_NETWORK_INTERFACE]->(:ProxmoxNetworkInterface)

    VMs have network interfaces. Use vmid to match.
    """

    target_node_label: str = "ProxmoxVM"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "vmid": PropertyRef("vmid"),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_NETWORK_INTERFACE"
    properties: ProxmoxNetworkInterfaceToVMRelProperties = (
        ProxmoxNetworkInterfaceToVMRelProperties()
    )


@dataclass(frozen=True)
class ProxmoxNetworkInterfaceSchema(CartographyNodeSchema):
    """
    Schema for a ProxmoxNetworkInterface.

    Network interfaces belong to VMs.
    """

    label: str = "ProxmoxNetworkInterface"
    properties: ProxmoxNetworkInterfaceNodeProperties = (
        ProxmoxNetworkInterfaceNodeProperties()
    )
    sub_resource_relationship: ProxmoxNetworkInterfaceToClusterRel = (
        ProxmoxNetworkInterfaceToClusterRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            ProxmoxNetworkInterfaceToVMRel(),
        ]
    )
