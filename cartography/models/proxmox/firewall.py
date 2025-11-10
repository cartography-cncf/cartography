"""
Data models for Proxmox firewall configurations.

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
from cartography.models.core.relationships import TargetNodeMatcher

# ============================================================================
# ProxmoxFirewallRule Node Schema
# ============================================================================


@dataclass(frozen=True)
class ProxmoxFirewallRuleNodeProperties(CartographyNodeProperties):
    """
    Properties for a ProxmoxFirewallRule node.

    Represents firewall rules at cluster, node, or VM level.
    """

    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    cluster_id: PropertyRef = PropertyRef("cluster_id")
    scope: PropertyRef = PropertyRef("scope")  # cluster, node, vm
    scope_id: PropertyRef = PropertyRef("scope_id")  # node name or vmid if applicable
    pos: PropertyRef = PropertyRef("pos")  # Position in rule list
    type: PropertyRef = PropertyRef("type")  # in, out, group
    action: PropertyRef = PropertyRef("action")  # ACCEPT, DROP, REJECT
    enable: PropertyRef = PropertyRef("enable")
    iface: PropertyRef = PropertyRef("iface")  # Network interface
    source: PropertyRef = PropertyRef("source")  # Source address/network
    dest: PropertyRef = PropertyRef("dest")  # Destination address/network
    proto: PropertyRef = PropertyRef("proto")  # Protocol (tcp, udp, icmp, etc.)
    sport: PropertyRef = PropertyRef("sport")  # Source port(s)
    dport: PropertyRef = PropertyRef("dport")  # Destination port(s)
    comment: PropertyRef = PropertyRef("comment")
    macro: PropertyRef = PropertyRef("macro")  # Predefined macro name
    log: PropertyRef = PropertyRef("log")  # Log level


@dataclass(frozen=True)
class ProxmoxFirewallRuleToClusterRelProperties(CartographyRelProperties):
    """
    Properties for relationship from ProxmoxFirewallRule to ProxmoxCluster.
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ProxmoxFirewallRuleToClusterRel(CartographyRelSchema):
    """
    Relationship: (:ProxmoxFirewallRule)-[:RESOURCE]->(:ProxmoxCluster)

    Firewall rules belong to clusters.
    """

    target_node_label: str = "ProxmoxCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("CLUSTER_ID", set_in_kwargs=True),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "RESOURCE"
    properties: ProxmoxFirewallRuleToClusterRelProperties = (
        ProxmoxFirewallRuleToClusterRelProperties()
    )


@dataclass(frozen=True)
class ProxmoxFirewallRuleSchema(CartographyNodeSchema):
    """
    Schema for ProxmoxFirewallRule.

    Firewall rules controlling network traffic.
    """

    label: str = "ProxmoxFirewallRule"
    properties: ProxmoxFirewallRuleNodeProperties = ProxmoxFirewallRuleNodeProperties()
    sub_resource_relationship: ProxmoxFirewallRuleToClusterRel = (
        ProxmoxFirewallRuleToClusterRel()
    )


# ============================================================================
# ProxmoxFirewallIPSet Node Schema
# ============================================================================


@dataclass(frozen=True)
class ProxmoxFirewallIPSetNodeProperties(CartographyNodeProperties):
    """
    Properties for a ProxmoxFirewallIPSet node.

    Represents IP sets (address groups) used in firewall rules.
    """

    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    cluster_id: PropertyRef = PropertyRef("cluster_id")
    scope: PropertyRef = PropertyRef("scope")  # cluster, node, vm
    scope_id: PropertyRef = PropertyRef("scope_id")
    comment: PropertyRef = PropertyRef("comment")
    cidrs: PropertyRef = PropertyRef("cidrs")  # Array of CIDR entries


@dataclass(frozen=True)
class ProxmoxFirewallIPSetToClusterRelProperties(CartographyRelProperties):
    """
    Properties for relationship from ProxmoxFirewallIPSet to ProxmoxCluster.
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ProxmoxFirewallIPSetToClusterRel(CartographyRelSchema):
    """
    Relationship: (:ProxmoxFirewallIPSet)-[:RESOURCE]->(:ProxmoxCluster)

    IP sets belong to clusters.
    """

    target_node_label: str = "ProxmoxCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("CLUSTER_ID", set_in_kwargs=True),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "RESOURCE"
    properties: ProxmoxFirewallIPSetToClusterRelProperties = (
        ProxmoxFirewallIPSetToClusterRelProperties()
    )


@dataclass(frozen=True)
class ProxmoxFirewallIPSetSchema(CartographyNodeSchema):
    """
    Schema for ProxmoxFirewallIPSet.

    IP address sets for use in firewall rules.
    """

    label: str = "ProxmoxFirewallIPSet"
    properties: ProxmoxFirewallIPSetNodeProperties = (
        ProxmoxFirewallIPSetNodeProperties()
    )
    sub_resource_relationship: ProxmoxFirewallIPSetToClusterRel = (
        ProxmoxFirewallIPSetToClusterRel()
    )
