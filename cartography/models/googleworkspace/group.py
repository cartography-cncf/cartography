from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_source_node_matcher
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import SourceNodeMatcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class GoogleWorkspaceGroupNodeProperties(CartographyNodeProperties):
    """
    Google Workspace group node properties
    Compatible with Cloud Identity API response structure
    """

    id: PropertyRef = PropertyRef("name")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)

    # Group identifiers and basic info
    email: PropertyRef = PropertyRef("email", extra_index=True)
    description: PropertyRef = PropertyRef("description")

    # Cloud Identity API fields
    name: PropertyRef = PropertyRef("name")
    display_name: PropertyRef = PropertyRef("displayName")
    parent: PropertyRef = PropertyRef("parent")
    create_time: PropertyRef = PropertyRef("createTime")
    update_time: PropertyRef = PropertyRef("updateTime")
    labels: PropertyRef = PropertyRef("labels")

    # Tenant relationship
    customer_id: PropertyRef = PropertyRef("CUSTOMER_ID", set_in_kwargs=True)


@dataclass(frozen=True)
class GoogleWorkspaceGroupToTenantRelProperties(CartographyRelProperties):
    """
    Properties for Google Workspace group to tenant relationship
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GoogleWorkspaceGroupToTenantRel(CartographyRelSchema):
    """
    Relationship from Google Workspace group to Google Workspace tenant
    """

    target_node_label: str = "GoogleWorkspaceTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("CUSTOMER_ID", set_in_kwargs=True),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GoogleWorkspaceGroupToTenantRelProperties = (
        GoogleWorkspaceGroupToTenantRelProperties()
    )


@dataclass(frozen=True)
class GoogleWorkspaceGroupToMemberRelProperties(CartographyRelProperties):
    """
    Properties for Google Workspace group to member relationship
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GoogleWorkspaceGroupToMemberRel(CartographyRelSchema):
    """
    Relationship from Google Workspace group to its members (users or groups)
    """

    target_node_label: str = (
        "GoogleWorkspaceUser"  # or GoogleWorkspaceGroup for subgroup relationships
    )
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "primary_email": PropertyRef("member_ids", one_to_many=True),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "MEMBER_OF"
    properties: GoogleWorkspaceGroupToMemberRelProperties = (
        GoogleWorkspaceGroupToMemberRelProperties()
    )


@dataclass(frozen=True)
class GoogleWorkspaceGroupToOwnerRelProperties(CartographyRelProperties):
    """
    Properties for Google Workspace group to owner relationship
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GoogleWorkspaceGroupToOwnerRel(CartographyRelSchema):
    """
    Relationship from Google Workspace group to its owners (users)
    """

    target_node_label: str = "GoogleWorkspaceUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "primary_email": PropertyRef("owner_ids", one_to_many=True),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "OWNER_OF"
    properties: GoogleWorkspaceGroupToOwnerRelProperties = (
        GoogleWorkspaceGroupToOwnerRelProperties()
    )


@dataclass(frozen=True)
class GoogleWorkspaceGroupSchema(CartographyNodeSchema):
    """
    Google Workspace group node schema
    """

    label: str = "GoogleWorkspaceGroup"
    properties: GoogleWorkspaceGroupNodeProperties = (
        GoogleWorkspaceGroupNodeProperties()
    )
    sub_resource_relationship: GoogleWorkspaceGroupToTenantRel = (
        GoogleWorkspaceGroupToTenantRel()
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["GCPPrincipal"])
    other_relationships = OtherRelationships(
        [
            GoogleWorkspaceGroupToMemberRel(),
            GoogleWorkspaceGroupToOwnerRel(),
        ]
    )


# MatchLinks for Group => Group relationships


@dataclass(frozen=True)
class GoogleWorkspaceGroupToGroupMemberRelProperties(CartographyRelProperties):
    """
    Properties for Google Workspace group to group member relationship (MatchLink)
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label", set_in_kwargs=True
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)
    role: PropertyRef = PropertyRef("role")


@dataclass(frozen=True)
class GoogleWorkspaceGroupToGroupMemberRel(CartographyRelSchema):
    """
    MatchLink relationship from Google Workspace parent group to member group
    """

    target_node_label: str = "GoogleWorkspaceGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "email": PropertyRef("subgroup_email"),
        }
    )
    source_node_label: str = "GoogleWorkspaceGroup"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {
            "id": PropertyRef("parent_group_id"),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "MEMBER_OF"
    properties: GoogleWorkspaceGroupToGroupMemberRelProperties = (
        GoogleWorkspaceGroupToGroupMemberRelProperties()
    )


@dataclass(frozen=True)
class GoogleWorkspaceGroupToGroupOwnerRelProperties(CartographyRelProperties):
    """
    Properties for Google Workspace group to group owner relationship (MatchLink)
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label", set_in_kwargs=True
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)
    role: PropertyRef = PropertyRef("role")


@dataclass(frozen=True)
class GoogleWorkspaceGroupToGroupOwnerRel(CartographyRelSchema):
    """
    MatchLink relationship from Google Workspace parent group to owner group
    """

    target_node_label: str = "GoogleWorkspaceGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "email": PropertyRef("subgroup_email"),
        }
    )
    source_node_label: str = "GoogleWorkspaceGroup"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {
            "id": PropertyRef("parent_group_id"),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "OWNER_OF"
    properties: GoogleWorkspaceGroupToGroupOwnerRelProperties = (
        GoogleWorkspaceGroupToGroupOwnerRelProperties()
    )


# Inherited relationship MatchLinks
@dataclass(frozen=True)
class GoogleWorkspaceUserToGroupInheritedMemberRelProperties(CartographyRelProperties):
    """
    Properties for inherited member relationship from user to group
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label", set_in_kwargs=True
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)


@dataclass(frozen=True)
class GoogleWorkspaceUserToGroupInheritedMemberRel(CartographyRelSchema):
    """
    MatchLink that creates INHERITED_MEMBER_OF relationships from users to groups
    they are indirectly members of through group hierarchy.

    Example: User -> MEMBER_OF -> SubGroup -> MEMBER_OF -> ParentGroup
    This creates: User -> INHERITED_MEMBER_OF -> ParentGroup
    """

    target_node_label: str = "GoogleWorkspaceGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("group_id")}
    )
    source_node_label: str = "GoogleWorkspaceUser"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("user_id")}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "INHERITED_MEMBER_OF"
    properties: GoogleWorkspaceUserToGroupInheritedMemberRelProperties = (
        GoogleWorkspaceUserToGroupInheritedMemberRelProperties()
    )


@dataclass(frozen=True)
class GoogleWorkspaceUserToGroupInheritedOwnerRelProperties(CartographyRelProperties):
    """
    Properties for inherited owner relationship from user to group
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label", set_in_kwargs=True
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)


@dataclass(frozen=True)
class GoogleWorkspaceUserToGroupInheritedOwnerRel(CartographyRelSchema):
    """
    MatchLink that creates INHERITED_OWNER_OF relationships from users to groups
    they are indirectly owners of through group hierarchy.

    Example: User -> OWNER_OF -> SubGroup -> MEMBER_OF -> ParentGroup
    This creates: User -> INHERITED_OWNER_OF -> ParentGroup
    """

    target_node_label: str = "GoogleWorkspaceGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("group_id")}
    )
    source_node_label: str = "GoogleWorkspaceUser"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("user_id")}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "INHERITED_OWNER_OF"
    properties: GoogleWorkspaceUserToGroupInheritedOwnerRelProperties = (
        GoogleWorkspaceUserToGroupInheritedOwnerRelProperties()
    )


@dataclass(frozen=True)
class GoogleWorkspaceGroupToGroupInheritedMemberRelProperties(CartographyRelProperties):
    """
    Properties for inherited member relationship from group to group
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label", set_in_kwargs=True
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)


@dataclass(frozen=True)
class GoogleWorkspaceGroupToGroupInheritedMemberRel(CartographyRelSchema):
    """
    MatchLink that creates INHERITED_MEMBER_OF relationships from groups to groups
    they are indirectly members of through group hierarchy.

    Example: SubGroup1 -> MEMBER_OF -> SubGroup2 -> MEMBER_OF -> ParentGroup
    This creates: SubGroup1 -> INHERITED_MEMBER_OF -> ParentGroup
    """

    target_node_label: str = "GoogleWorkspaceGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("target_group_id")}
    )
    source_node_label: str = "GoogleWorkspaceGroup"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("source_group_id")}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "INHERITED_MEMBER_OF"
    properties: GoogleWorkspaceGroupToGroupInheritedMemberRelProperties = (
        GoogleWorkspaceGroupToGroupInheritedMemberRelProperties()
    )


@dataclass(frozen=True)
class GoogleWorkspaceGroupToGroupInheritedOwnerRelProperties(CartographyRelProperties):
    """
    Properties for inherited owner relationship from group to group
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label", set_in_kwargs=True
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)


@dataclass(frozen=True)
class GoogleWorkspaceGroupToGroupInheritedOwnerRel(CartographyRelSchema):
    """
    MatchLink that creates INHERITED_OWNER_OF relationships from groups to groups
    they are indirectly owners of through group hierarchy.

    Example: SubGroup1 -> OWNER_OF -> SubGroup2 -> MEMBER_OF -> ParentGroup
    This creates: SubGroup1 -> INHERITED_OWNER_OF -> ParentGroup
    """

    target_node_label: str = "GoogleWorkspaceGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("target_group_id")}
    )
    source_node_label: str = "GoogleWorkspaceGroup"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("source_group_id")}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "INHERITED_OWNER_OF"
    properties: GoogleWorkspaceGroupToGroupInheritedOwnerRelProperties = (
        GoogleWorkspaceGroupToGroupInheritedOwnerRelProperties()
    )
