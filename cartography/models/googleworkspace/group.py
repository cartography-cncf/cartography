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
    """

    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)

    # Group identifiers and basic info
    group_id: PropertyRef = PropertyRef("id")  # Alias for id
    email: PropertyRef = PropertyRef("email", extra_index=True)
    name: PropertyRef = PropertyRef("name")
    description: PropertyRef = PropertyRef("description")

    # Group settings
    admin_created: PropertyRef = PropertyRef("adminCreated")
    direct_members_count: PropertyRef = PropertyRef("directMembersCount")

    # Metadata
    etag: PropertyRef = PropertyRef("etag")
    kind: PropertyRef = PropertyRef("kind")

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
    direction: LinkDirection = LinkDirection.OUTWARD
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
            "id": PropertyRef("member_ids", one_to_many=True),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "MEMBER_GOOGLEWORKSPACE_GROUP"
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
            "id": PropertyRef("owner_ids", one_to_many=True),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "OWNER_GOOGLEWORKSPACE_GROUP"
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
            "id": PropertyRef("subgroup_id"),
        }
    )
    source_node_label: str = "GoogleWorkspaceGroup"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {
            "id": PropertyRef("parent_group_id"),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "MEMBER_GOOGLEWORKSPACE_GROUP"
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
            "id": PropertyRef("subgroup_id"),
        }
    )
    source_node_label: str = "GoogleWorkspaceGroup"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {
            "id": PropertyRef("parent_group_id"),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "OWNER_GOOGLEWORKSPACE_GROUP"
    properties: GoogleWorkspaceGroupToGroupOwnerRelProperties = (
        GoogleWorkspaceGroupToGroupOwnerRelProperties()
    )
