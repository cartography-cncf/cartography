"""
Data models for Proxmox storage resources.

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
# ProxmoxStorage Node Schema
# ============================================================================

@dataclass(frozen=True)
class ProxmoxStorageNodeProperties(CartographyNodeProperties):
    """
    Properties for a ProxmoxStorage node.
    """
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    cluster_id: PropertyRef = PropertyRef("cluster_id")
    type: PropertyRef = PropertyRef("type")
    content_types: PropertyRef = PropertyRef("content_types")
    shared: PropertyRef = PropertyRef("shared")
    enabled: PropertyRef = PropertyRef("enabled")
    total: PropertyRef = PropertyRef("total")
    used: PropertyRef = PropertyRef("used")
    available: PropertyRef = PropertyRef("available")


@dataclass(frozen=True)
class ProxmoxStorageToClusterRelProperties(CartographyRelProperties):
    """
    Properties for relationship from ProxmoxStorage to ProxmoxCluster.
    """
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ProxmoxStorageToClusterRel(CartographyRelSchema):
    """
    Relationship: (:ProxmoxStorage)-[:RESOURCE]->(:ProxmoxCluster)
    
    Storage belongs to clusters.
    """
    target_node_label: str = "ProxmoxCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher({
        "id": PropertyRef("CLUSTER_ID", set_in_kwargs=True),
    })
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "RESOURCE"
    properties: ProxmoxStorageToClusterRelProperties = ProxmoxStorageToClusterRelProperties()


@dataclass(frozen=True)
class ProxmoxStorageSchema(CartographyNodeSchema):
    """
    Schema for ProxmoxStorage.
    
    Storage resources belong to clusters and are available on nodes.
    Note: The AVAILABLE_ON relationship to nodes is created separately via
    load_storage_node_relationships() since it's a many-to-many relationship.
    """
    label: str = "ProxmoxStorage"
    properties: ProxmoxStorageNodeProperties = ProxmoxStorageNodeProperties()
    sub_resource_relationship: ProxmoxStorageToClusterRel = ProxmoxStorageToClusterRel()
