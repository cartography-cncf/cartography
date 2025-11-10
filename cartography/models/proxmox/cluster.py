"""
Data models for Proxmox clusters and nodes.

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
# ProxmoxCluster Node Schema
# ============================================================================


@dataclass(frozen=True)
class ProxmoxClusterNodeProperties(CartographyNodeProperties):
    """
    Properties for a ProxmoxCluster node.

    Per AGENTS.md:
    - Use PropertyRef for all properties
    - Required fields use direct key access in transform
    - Optional fields use .get() in transform
    """

    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    version: PropertyRef = PropertyRef("version")
    quorate: PropertyRef = PropertyRef("quorate")
    nodes_online: PropertyRef = PropertyRef("nodes_online")
    nodes_total: PropertyRef = PropertyRef("nodes_total")  # Total nodes in cluster
    cluster_id: PropertyRef = PropertyRef("cluster_id")  # Internal cluster ID from API

    # Cluster options/configuration
    migration_type: PropertyRef = PropertyRef(
        "migration_type"
    )  # Migration type (secure, insecure)
    migration_network: PropertyRef = PropertyRef(
        "migration_network"
    )  # Migration network CIDR
    migration_bandwidth_limit: PropertyRef = PropertyRef(
        "migration_bandwidth_limit"
    )  # Migration bandwidth limit
    console: PropertyRef = PropertyRef("console")  # Default console type
    email_from: PropertyRef = PropertyRef("email_from")  # Email from address
    http_proxy: PropertyRef = PropertyRef("http_proxy")  # HTTP proxy
    keyboard: PropertyRef = PropertyRef("keyboard")  # Keyboard layout
    language: PropertyRef = PropertyRef("language")  # Default language
    mac_prefix: PropertyRef = PropertyRef("mac_prefix")  # MAC address prefix
    max_workers: PropertyRef = PropertyRef("max_workers")  # Maximum workers
    next_id_lower: PropertyRef = PropertyRef("next_id_lower")  # Next VMID lower bound
    next_id_upper: PropertyRef = PropertyRef("next_id_upper")  # Next VMID upper bound

    # Corosync/Totem configuration
    totem_interface: PropertyRef = PropertyRef(
        "totem_interface"
    )  # Totem interface configuration
    totem_cluster_name: PropertyRef = PropertyRef(
        "totem_cluster_name"
    )  # Totem cluster name
    totem_config_version: PropertyRef = PropertyRef(
        "totem_config_version"
    )  # Totem config version
    totem_ip_version: PropertyRef = PropertyRef(
        "totem_ip_version"
    )  # IP version (ipv4/ipv6)
    totem_secauth: PropertyRef = PropertyRef(
        "totem_secauth"
    )  # Security authentication enabled
    totem_version: PropertyRef = PropertyRef("totem_version")  # Totem version


@dataclass(frozen=True)
class ProxmoxClusterSchema(CartographyNodeSchema):
    """
    Schema for a ProxmoxCluster node.

    Proxmox clusters are the top-level tenant-like entity.
    No sub_resource_relationship needed as this is the root.
    """

    label: str = "ProxmoxCluster"
    properties: ProxmoxClusterNodeProperties = ProxmoxClusterNodeProperties()
    # No sub_resource_relationship - this is the tenant-like root entity
    sub_resource_relationship: None = None


# ============================================================================
# ProxmoxNode Node Schema
# ============================================================================


@dataclass(frozen=True)
class ProxmoxNodeNodeProperties(CartographyNodeProperties):
    """
    Properties for a ProxmoxNode.
    """

    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    cluster_id: PropertyRef = PropertyRef("cluster_id")
    hostname: PropertyRef = PropertyRef("hostname")
    ip: PropertyRef = PropertyRef("ip")
    status: PropertyRef = PropertyRef("status")
    uptime: PropertyRef = PropertyRef("uptime")
    cpu_count: PropertyRef = PropertyRef("cpu_count")
    cpu_usage: PropertyRef = PropertyRef("cpu_usage")
    memory_total: PropertyRef = PropertyRef("memory_total")
    memory_used: PropertyRef = PropertyRef("memory_used")
    disk_total: PropertyRef = PropertyRef("disk_total")
    disk_used: PropertyRef = PropertyRef("disk_used")
    level: PropertyRef = PropertyRef("level")
    # Additional node information
    kversion: PropertyRef = PropertyRef("kversion")  # Kernel version
    loadavg: PropertyRef = PropertyRef("loadavg")  # Load average (comma-separated)
    wait: PropertyRef = PropertyRef("wait")  # I/O wait time
    # Swap information
    swap_total: PropertyRef = PropertyRef("swap_total")  # Total swap space
    swap_used: PropertyRef = PropertyRef("swap_used")  # Used swap space
    swap_free: PropertyRef = PropertyRef("swap_free")  # Free swap space
    # Additional system info
    pveversion: PropertyRef = PropertyRef("pveversion")  # PVE version
    cpuinfo: PropertyRef = PropertyRef("cpuinfo")  # CPU model info
    idle: PropertyRef = PropertyRef("idle")  # Idle CPU percentage


@dataclass(frozen=True)
class ProxmoxNodeToClusterRelProperties(CartographyRelProperties):
    """
    Properties for relationship from ProxmoxNode to ProxmoxCluster.
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ProxmoxNodeToClusterRel(CartographyRelSchema):
    """
    Relationship: (:ProxmoxNode)-[:RESOURCE]->(:ProxmoxCluster)

    Per AGENTS.md: sub_resource_relationship should always point to tenant-like object.
    ProxmoxCluster is the tenant-like entity for Proxmox resources.
    """

    target_node_label: str = "ProxmoxCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("CLUSTER_ID", set_in_kwargs=True),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "RESOURCE"
    properties: ProxmoxNodeToClusterRelProperties = ProxmoxNodeToClusterRelProperties()


@dataclass(frozen=True)
class ProxmoxNodeSchema(CartographyNodeSchema):
    """
    Schema for a ProxmoxNode.

    Nodes belong to clusters and host VMs/containers.
    """

    label: str = "ProxmoxNode"
    properties: ProxmoxNodeNodeProperties = ProxmoxNodeNodeProperties()
    sub_resource_relationship: ProxmoxNodeToClusterRel = ProxmoxNodeToClusterRel()


# ============================================================================
# ProxmoxNodeNetworkInterface Node Schema
# ============================================================================


@dataclass(frozen=True)
class ProxmoxNodeNetworkInterfaceNodeProperties(CartographyNodeProperties):
    """
    Properties for a ProxmoxNodeNetworkInterface.

    Represents physical/virtual network interfaces on Proxmox nodes.
    """

    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name", extra_index=True
    )  # Interface name (e.g., vmbr0, eth0)
    node_name: PropertyRef = PropertyRef("node_name")
    type: PropertyRef = PropertyRef("type")  # bridge, bond, eth, vlan, etc.
    address: PropertyRef = PropertyRef("address")  # IPv4 address
    netmask: PropertyRef = PropertyRef("netmask")  # Subnet mask
    gateway: PropertyRef = PropertyRef("gateway")  # Default gateway
    address6: PropertyRef = PropertyRef("address6")  # IPv6 address
    netmask6: PropertyRef = PropertyRef("netmask6")  # IPv6 netmask
    gateway6: PropertyRef = PropertyRef("gateway6")  # IPv6 gateway
    bridge_ports: PropertyRef = PropertyRef("bridge_ports")  # Bridge member ports
    bond_slaves: PropertyRef = PropertyRef("bond_slaves")  # Bond slave interfaces
    active: PropertyRef = PropertyRef("active")  # Interface active status
    autostart: PropertyRef = PropertyRef("autostart")  # Auto-start on boot
    mtu: PropertyRef = PropertyRef("mtu")  # MTU size
    # Additional bond configuration
    bond_mode: PropertyRef = PropertyRef(
        "bond_mode"
    )  # Bonding mode (balance-rr, active-backup, etc.)
    bond_xmit_hash_policy: PropertyRef = PropertyRef(
        "bond_xmit_hash_policy"
    )  # Bond hashing policy
    # Additional network config
    cidr: PropertyRef = PropertyRef("cidr")  # CIDR notation (IPv4)
    cidr6: PropertyRef = PropertyRef("cidr6")  # CIDR notation (IPv6)
    method: PropertyRef = PropertyRef(
        "method"
    )  # Configuration method (static, dhcp, manual)
    method6: PropertyRef = PropertyRef("method6")  # IPv6 configuration method
    comments: PropertyRef = PropertyRef("comments")  # Interface comments


@dataclass(frozen=True)
class ProxmoxNodeNetworkInterfaceToClusterRelProperties(CartographyRelProperties):
    """
    Properties for relationship from ProxmoxNodeNetworkInterface to ProxmoxCluster.
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ProxmoxNodeNetworkInterfaceToClusterRel(CartographyRelSchema):
    """
    Relationship: (:ProxmoxNodeNetworkInterface)-[:RESOURCE]->(:ProxmoxCluster)
    """

    target_node_label: str = "ProxmoxCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("CLUSTER_ID", set_in_kwargs=True),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "RESOURCE"
    properties: ProxmoxNodeNetworkInterfaceToClusterRelProperties = (
        ProxmoxNodeNetworkInterfaceToClusterRelProperties()
    )


@dataclass(frozen=True)
class ProxmoxNodeNetworkInterfaceToNodeRelProperties(CartographyRelProperties):
    """
    Properties for relationship from ProxmoxNode to ProxmoxNodeNetworkInterface.
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ProxmoxNodeNetworkInterfaceToNodeRel(CartographyRelSchema):
    """
    Relationship: (:ProxmoxNode)-[:HAS_NETWORK_INTERFACE]->(:ProxmoxNodeNetworkInterface)

    Nodes have physical/virtual network interfaces.
    """

    target_node_label: str = "ProxmoxNode"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("node_name"),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_NETWORK_INTERFACE"
    properties: ProxmoxNodeNetworkInterfaceToNodeRelProperties = (
        ProxmoxNodeNetworkInterfaceToNodeRelProperties()
    )


@dataclass(frozen=True)
class ProxmoxNodeNetworkInterfaceSchema(CartographyNodeSchema):
    """
    Schema for ProxmoxNodeNetworkInterface.

    Network interfaces belong to nodes.
    """

    label: str = "ProxmoxNodeNetworkInterface"
    properties: ProxmoxNodeNetworkInterfaceNodeProperties = (
        ProxmoxNodeNetworkInterfaceNodeProperties()
    )
    sub_resource_relationship: ProxmoxNodeNetworkInterfaceToClusterRel = (
        ProxmoxNodeNetworkInterfaceToClusterRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            ProxmoxNodeNetworkInterfaceToNodeRel(),
        ]
    )
