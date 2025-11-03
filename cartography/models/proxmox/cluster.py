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
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher({
        "id": PropertyRef("CLUSTER_ID", set_in_kwargs=True),
    })
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
    name: PropertyRef = PropertyRef("name", extra_index=True)  # Interface name (e.g., vmbr0, eth0)
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
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher({
        "id": PropertyRef("CLUSTER_ID", set_in_kwargs=True),
    })
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
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher({
        "id": PropertyRef("node_name"),
    })
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
    properties: ProxmoxNodeNetworkInterfaceNodeProperties = ProxmoxNodeNetworkInterfaceNodeProperties()
    sub_resource_relationship: ProxmoxNodeNetworkInterfaceToClusterRel = (
        ProxmoxNodeNetworkInterfaceToClusterRel()
    )
    other_relationships: OtherRelationships = OtherRelationships([
        ProxmoxNodeNetworkInterfaceToNodeRel(),
    ])
