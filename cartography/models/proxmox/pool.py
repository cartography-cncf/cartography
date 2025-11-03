"""
Data models for Proxmox resource pools.

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
# ProxmoxPool Node Schema
# ============================================================================

@dataclass(frozen=True)
class ProxmoxPoolNodeProperties(CartographyNodeProperties):
    """
    Properties for a ProxmoxPool node.
    
    Resource pools are used to organize VMs, containers, and storage.
    """
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    poolid: PropertyRef = PropertyRef("poolid", extra_index=True)
    comment: PropertyRef = PropertyRef("comment")
    cluster_id: PropertyRef = PropertyRef("cluster_id")


@dataclass(frozen=True)
class ProxmoxPoolToClusterRelProperties(CartographyRelProperties):
    """
    Properties for relationship from ProxmoxPool to ProxmoxCluster.
    """
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ProxmoxPoolToClusterRel(CartographyRelSchema):
    """
    Relationship: (:ProxmoxPool)-[:RESOURCE]->(:ProxmoxCluster)
    
    Pools belong to clusters.
    """
    target_node_label: str = "ProxmoxCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher({
        "id": PropertyRef("CLUSTER_ID", set_in_kwargs=True),
    })
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "RESOURCE"
    properties: ProxmoxPoolToClusterRelProperties = ProxmoxPoolToClusterRelProperties()


@dataclass(frozen=True)
class ProxmoxPoolSchema(CartographyNodeSchema):
    """
    Schema for ProxmoxPool.
    
    Pools organize VMs, containers, and storage resources.
    """
    label: str = "ProxmoxPool"
    properties: ProxmoxPoolNodeProperties = ProxmoxPoolNodeProperties()
    sub_resource_relationship: ProxmoxPoolToClusterRel = ProxmoxPoolToClusterRel()
