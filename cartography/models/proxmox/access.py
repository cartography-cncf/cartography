"""
Data models for Proxmox access control (users, groups, roles, ACLs).

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
# ProxmoxUser Node Schema
# ============================================================================


@dataclass(frozen=True)
class ProxmoxUserNodeProperties(CartographyNodeProperties):
    """
    Properties for a ProxmoxUser node.

    Represents user accounts in Proxmox VE.
    """

    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    userid: PropertyRef = PropertyRef("userid", extra_index=True)
    cluster_id: PropertyRef = PropertyRef("cluster_id")
    enable: PropertyRef = PropertyRef("enable")
    expire: PropertyRef = PropertyRef("expire")
    firstname: PropertyRef = PropertyRef("firstname")
    lastname: PropertyRef = PropertyRef("lastname")
    email: PropertyRef = PropertyRef("email", extra_index=True)
    comment: PropertyRef = PropertyRef("comment")
    groups: PropertyRef = PropertyRef("groups")  # Array of group memberships
    tokens: PropertyRef = PropertyRef("tokens")  # Array of API tokens


@dataclass(frozen=True)
class ProxmoxUserToClusterRelProperties(CartographyRelProperties):
    """
    Properties for relationship from ProxmoxUser to ProxmoxCluster.
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ProxmoxUserToClusterRel(CartographyRelSchema):
    """
    Relationship: (:ProxmoxUser)-[:RESOURCE]->(:ProxmoxCluster)

    Users belong to clusters.
    """

    target_node_label: str = "ProxmoxCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("CLUSTER_ID", set_in_kwargs=True),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "RESOURCE"
    properties: ProxmoxUserToClusterRelProperties = ProxmoxUserToClusterRelProperties()


@dataclass(frozen=True)
class ProxmoxUserToGroupRelProperties(CartographyRelProperties):
    """
    Properties for relationship from ProxmoxUser to ProxmoxGroup.
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ProxmoxUserToGroupRel(CartographyRelSchema):
    """
    Relationship: (:ProxmoxUser)-[:MEMBER_OF_GROUP]->(:ProxmoxGroup)

    Users are members of groups.
    """

    target_node_label: str = "ProxmoxGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "groupid": PropertyRef("groups", one_to_many=True),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MEMBER_OF_GROUP"
    properties: ProxmoxUserToGroupRelProperties = ProxmoxUserToGroupRelProperties()


@dataclass(frozen=True)
class ProxmoxUserSchema(CartographyNodeSchema):
    """
    Schema for ProxmoxUser.

    User accounts for Proxmox VE authentication and authorization.
    """

    label: str = "ProxmoxUser"
    properties: ProxmoxUserNodeProperties = ProxmoxUserNodeProperties()
    sub_resource_relationship: ProxmoxUserToClusterRel = ProxmoxUserToClusterRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            ProxmoxUserToGroupRel(),
        ]
    )


# ============================================================================
# ProxmoxGroup Node Schema
# ============================================================================


@dataclass(frozen=True)
class ProxmoxGroupNodeProperties(CartographyNodeProperties):
    """
    Properties for a ProxmoxGroup node.

    Represents user groups in Proxmox VE.
    """

    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    groupid: PropertyRef = PropertyRef("groupid", extra_index=True)
    cluster_id: PropertyRef = PropertyRef("cluster_id")
    comment: PropertyRef = PropertyRef("comment")


@dataclass(frozen=True)
class ProxmoxGroupToClusterRelProperties(CartographyRelProperties):
    """
    Properties for relationship from ProxmoxGroup to ProxmoxCluster.
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ProxmoxGroupToClusterRel(CartographyRelSchema):
    """
    Relationship: (:ProxmoxGroup)-[:RESOURCE]->(:ProxmoxCluster)

    Groups belong to clusters.
    """

    target_node_label: str = "ProxmoxCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("CLUSTER_ID", set_in_kwargs=True),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "RESOURCE"
    properties: ProxmoxGroupToClusterRelProperties = (
        ProxmoxGroupToClusterRelProperties()
    )


@dataclass(frozen=True)
class ProxmoxGroupSchema(CartographyNodeSchema):
    """
    Schema for ProxmoxGroup.

    User groups for organizing permissions in Proxmox VE.
    """

    label: str = "ProxmoxGroup"
    properties: ProxmoxGroupNodeProperties = ProxmoxGroupNodeProperties()
    sub_resource_relationship: ProxmoxGroupToClusterRel = ProxmoxGroupToClusterRel()


# ============================================================================
# ProxmoxRole Node Schema
# ============================================================================


@dataclass(frozen=True)
class ProxmoxRoleNodeProperties(CartographyNodeProperties):
    """
    Properties for a ProxmoxRole node.

    Represents permission roles in Proxmox VE.
    """

    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    roleid: PropertyRef = PropertyRef("roleid", extra_index=True)
    cluster_id: PropertyRef = PropertyRef("cluster_id")
    privs: PropertyRef = PropertyRef("privs")  # Array of privileges
    special: PropertyRef = PropertyRef("special")  # Built-in role flag


@dataclass(frozen=True)
class ProxmoxRoleToClusterRelProperties(CartographyRelProperties):
    """
    Properties for relationship from ProxmoxRole to ProxmoxCluster.
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ProxmoxRoleToClusterRel(CartographyRelSchema):
    """
    Relationship: (:ProxmoxRole)-[:RESOURCE]->(:ProxmoxCluster)

    Roles belong to clusters.
    """

    target_node_label: str = "ProxmoxCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("CLUSTER_ID", set_in_kwargs=True),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "RESOURCE"
    properties: ProxmoxRoleToClusterRelProperties = ProxmoxRoleToClusterRelProperties()


@dataclass(frozen=True)
class ProxmoxRoleSchema(CartographyNodeSchema):
    """
    Schema for ProxmoxRole.

    Permission roles defining what actions users can perform.
    """

    label: str = "ProxmoxRole"
    properties: ProxmoxRoleNodeProperties = ProxmoxRoleNodeProperties()
    sub_resource_relationship: ProxmoxRoleToClusterRel = ProxmoxRoleToClusterRel()


# ============================================================================
# ProxmoxACL Node Schema
# ============================================================================


@dataclass(frozen=True)
class ProxmoxACLNodeProperties(CartographyNodeProperties):
    """
    Properties for a ProxmoxACL node.

    Represents Access Control List entries granting permissions.
    """

    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    path: PropertyRef = PropertyRef("path", extra_index=True)
    cluster_id: PropertyRef = PropertyRef("cluster_id")
    roleid: PropertyRef = PropertyRef("roleid")
    ugid: PropertyRef = PropertyRef("ugid", extra_index=True)  # User or group ID (indexed for queries)
    propagate: PropertyRef = PropertyRef("propagate")  # Propagate to children
    principal_type: PropertyRef = PropertyRef("principal_type")  # "user" or "group"
    resource_type: PropertyRef = PropertyRef("resource_type")  # Type of resource (vm, storage, pool, node, etc.)
    resource_id: PropertyRef = PropertyRef("resource_id")  # Specific resource ID if applicable


@dataclass(frozen=True)
class ProxmoxACLToClusterRelProperties(CartographyRelProperties):
    """
    Properties for relationship from ProxmoxACL to ProxmoxCluster.
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ProxmoxACLToClusterRel(CartographyRelSchema):
    """
    Relationship: (:ProxmoxACL)-[:RESOURCE]->(:ProxmoxCluster)

    ACLs belong to clusters.
    """

    target_node_label: str = "ProxmoxCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("CLUSTER_ID", set_in_kwargs=True),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "RESOURCE"
    properties: ProxmoxACLToClusterRelProperties = ProxmoxACLToClusterRelProperties()


@dataclass(frozen=True)
class ProxmoxACLToRoleRelProperties(CartographyRelProperties):
    """
    Properties for relationship from ProxmoxACL to ProxmoxRole.
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ProxmoxACLToRoleRel(CartographyRelSchema):
    """
    Relationship: (:ProxmoxACL)-[:GRANTS_ROLE]->(:ProxmoxRole)

    ACLs grant roles to users/groups.
    Includes metadata about permission scope and propagation.
    """

    target_node_label: str = "ProxmoxRole"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "roleid": PropertyRef("roleid"),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "GRANTS_ROLE"
    properties: ProxmoxACLToRoleRelProperties = ProxmoxACLToRoleRelProperties()


@dataclass(frozen=True)
class ProxmoxACLSchema(CartographyNodeSchema):
    """
    Schema for ProxmoxACL.

    Access Control List entries defining permissions.
    """

    label: str = "ProxmoxACL"
    properties: ProxmoxACLNodeProperties = ProxmoxACLNodeProperties()
    sub_resource_relationship: ProxmoxACLToClusterRel = ProxmoxACLToClusterRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            ProxmoxACLToRoleRel(),
        ]
    )
