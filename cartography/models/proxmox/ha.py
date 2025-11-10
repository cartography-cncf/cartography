"""
Data models for Proxmox High Availability (HA) resources.

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
# ProxmoxHAGroup Node Schema
# ============================================================================


@dataclass(frozen=True)
class ProxmoxHAGroupNodeProperties(CartographyNodeProperties):
    """
    Properties for a ProxmoxHAGroup node.

    HA groups define node preferences for high availability resources.
    """

    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    group: PropertyRef = PropertyRef("group", extra_index=True)
    cluster_id: PropertyRef = PropertyRef("cluster_id")
    nodes: PropertyRef = PropertyRef("nodes")  # Preferred node list
    restricted: PropertyRef = PropertyRef("restricted")  # Restrict to listed nodes
    nofailback: PropertyRef = PropertyRef("nofailback")  # Prevent failback
    comment: PropertyRef = PropertyRef("comment")


@dataclass(frozen=True)
class ProxmoxHAGroupToClusterRelProperties(CartographyRelProperties):
    """
    Properties for relationship from ProxmoxHAGroup to ProxmoxCluster.
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ProxmoxHAGroupToClusterRel(CartographyRelSchema):
    """
    Relationship: (:ProxmoxHAGroup)-[:RESOURCE]->(:ProxmoxCluster)

    HA groups belong to clusters.
    """

    target_node_label: str = "ProxmoxCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("CLUSTER_ID", set_in_kwargs=True),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "RESOURCE"
    properties: ProxmoxHAGroupToClusterRelProperties = (
        ProxmoxHAGroupToClusterRelProperties()
    )


@dataclass(frozen=True)
class ProxmoxHAGroupSchema(CartographyNodeSchema):
    """
    Schema for ProxmoxHAGroup.

    HA groups organize nodes for high availability resource placement.
    """

    label: str = "ProxmoxHAGroup"
    properties: ProxmoxHAGroupNodeProperties = ProxmoxHAGroupNodeProperties()
    sub_resource_relationship: ProxmoxHAGroupToClusterRel = ProxmoxHAGroupToClusterRel()


# ============================================================================
# ProxmoxHAResource Node Schema
# ============================================================================


@dataclass(frozen=True)
class ProxmoxHAResourceNodeProperties(CartographyNodeProperties):
    """
    Properties for a ProxmoxHAResource node.

    Represents VMs/containers configured for high availability.
    """

    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    sid: PropertyRef = PropertyRef("sid", extra_index=True)  # Service ID (vm:vmid)
    cluster_id: PropertyRef = PropertyRef("cluster_id")
    state: PropertyRef = PropertyRef("state")  # started, stopped, disabled, etc.
    group: PropertyRef = PropertyRef("group")  # Associated HA group
    max_restart: PropertyRef = PropertyRef("max_restart")
    max_relocate: PropertyRef = PropertyRef("max_relocate")
    comment: PropertyRef = PropertyRef("comment")


@dataclass(frozen=True)
class ProxmoxHAResourceToClusterRelProperties(CartographyRelProperties):
    """
    Properties for relationship from ProxmoxHAResource to ProxmoxCluster.
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ProxmoxHAResourceToClusterRel(CartographyRelSchema):
    """
    Relationship: (:ProxmoxHAResource)-[:RESOURCE]->(:ProxmoxCluster)

    HA resources belong to clusters.
    """

    target_node_label: str = "ProxmoxCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("CLUSTER_ID", set_in_kwargs=True),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "RESOURCE"
    properties: ProxmoxHAResourceToClusterRelProperties = (
        ProxmoxHAResourceToClusterRelProperties()
    )


@dataclass(frozen=True)
class ProxmoxHAResourceToHAGroupRelProperties(CartographyRelProperties):
    """
    Properties for relationship from ProxmoxHAResource to ProxmoxHAGroup.
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ProxmoxHAResourceToHAGroupRel(CartographyRelSchema):
    """
    Relationship: (:ProxmoxHAResource)-[:MEMBER_OF_HA_GROUP]->(:ProxmoxHAGroup)

    HA resources are assigned to HA groups.
    """

    target_node_label: str = "ProxmoxHAGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "group": PropertyRef("group"),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MEMBER_OF_HA_GROUP"
    properties: ProxmoxHAResourceToHAGroupRelProperties = (
        ProxmoxHAResourceToHAGroupRelProperties()
    )


@dataclass(frozen=True)
class ProxmoxHAResourceSchema(CartographyNodeSchema):
    """
    Schema for ProxmoxHAResource.

    HA resources represent VMs/containers configured for high availability.
    """

    label: str = "ProxmoxHAResource"
    properties: ProxmoxHAResourceNodeProperties = ProxmoxHAResourceNodeProperties()
    sub_resource_relationship: ProxmoxHAResourceToClusterRel = (
        ProxmoxHAResourceToClusterRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            ProxmoxHAResourceToHAGroupRel(),
        ]
    )
