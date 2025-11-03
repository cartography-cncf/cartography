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
    memory: PropertyRef = PropertyRef("memory")
    disk_size: PropertyRef = PropertyRef("disk_size")
    uptime: PropertyRef = PropertyRef("uptime")
    tags: PropertyRef = PropertyRef("tags")


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
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher({
        "id": PropertyRef("CLUSTER_ID", set_in_kwargs=True),
    })
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
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher({
        "id": PropertyRef("node"),
    })
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
    other_relationships: OtherRelationships = OtherRelationships([
        ProxmoxVMToNodeRel(),
    ])


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
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher({
        "id": PropertyRef("CLUSTER_ID", set_in_kwargs=True),
    })
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
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher({
        "vmid": PropertyRef("vmid"),
    })
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
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher({
        "id": PropertyRef("storage"),
    })
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
    other_relationships: OtherRelationships = OtherRelationships([
        ProxmoxDiskToVMRel(),
        ProxmoxDiskToStorageRel(),
    ])


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
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher({
        "id": PropertyRef("CLUSTER_ID", set_in_kwargs=True),
    })
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "RESOURCE"
    properties: ProxmoxNetworkInterfaceToClusterRelProperties = ProxmoxNetworkInterfaceToClusterRelProperties()


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
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher({
        "vmid": PropertyRef("vmid"),
    })
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_NETWORK_INTERFACE"
    properties: ProxmoxNetworkInterfaceToVMRelProperties = ProxmoxNetworkInterfaceToVMRelProperties()


@dataclass(frozen=True)
class ProxmoxNetworkInterfaceSchema(CartographyNodeSchema):
    """
    Schema for a ProxmoxNetworkInterface.
    
    Network interfaces belong to VMs.
    """
    label: str = "ProxmoxNetworkInterface"
    properties: ProxmoxNetworkInterfaceNodeProperties = ProxmoxNetworkInterfaceNodeProperties()
    sub_resource_relationship: ProxmoxNetworkInterfaceToClusterRel = ProxmoxNetworkInterfaceToClusterRel()
    other_relationships: OtherRelationships = OtherRelationships([
        ProxmoxNetworkInterfaceToVMRel(),
    ])
