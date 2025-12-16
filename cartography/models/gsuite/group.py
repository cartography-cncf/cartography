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
class GSuiteGroupNodeProperties(CartographyNodeProperties):
    """
    GSuite group node properties
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
class GSuiteGroupToTenantRelProperties(CartographyRelProperties):
    """
    Properties for GSuite group to tenant relationship
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GSuiteGroupToTenantRel(CartographyRelSchema):
    """
    Relationship from GSuite group to GSuite tenant
    """

    target_node_label: str = "GSuiteTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("CUSTOMER_ID", set_in_kwargs=True),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "RESOURCE"
    properties: GSuiteGroupToTenantRelProperties = GSuiteGroupToTenantRelProperties()


@dataclass(frozen=True)
class GSuiteGroupToMemberRelProperties(CartographyRelProperties):
    """
    Properties for GSuite group to member relationship
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GSuiteGroupToMemberRel(CartographyRelSchema):
    """
    Relationship from GSuite group to its members (users or groups)
    """

    target_node_label: str = "GSuiteUser"  # or GSuiteGroup for subgroup relationships
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("member_ids", one_to_many=True),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "MEMBER_GSUITE_GROUP"
    properties: GSuiteGroupToMemberRelProperties = GSuiteGroupToMemberRelProperties()


@dataclass(frozen=True)
class GSuiteGroupToOwnerRelProperties(CartographyRelProperties):
    """
    Properties for GSuite group to owner relationship
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GSuiteGroupToOwnerRel(CartographyRelSchema):
    """
    Relationship from GSuite group to its owners (users)
    """

    target_node_label: str = "GSuiteUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("owner_ids", one_to_many=True),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "OWNER_GSUITE_GROUP"
    properties: GSuiteGroupToOwnerRelProperties = GSuiteGroupToOwnerRelProperties()


@dataclass(frozen=True)
class GSuiteGroupSchema(CartographyNodeSchema):
    """
    GSuite group node schema
    """

    label: str = "GSuiteGroup"
    properties: GSuiteGroupNodeProperties = GSuiteGroupNodeProperties()
    sub_resource_relationship: GSuiteGroupToTenantRel = GSuiteGroupToTenantRel()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["GCPPrincipal"])
    other_relationships = OtherRelationships(
        [
            GSuiteGroupToMemberRel(),
            GSuiteGroupToOwnerRel(),
        ]
    )


# MatchLinks for Group => Group relationships


@dataclass(frozen=True)
class GSuiteGroupToGroupMemberRelProperties(CartographyRelProperties):
    """
    Properties for GSuite group to group member relationship (MatchLink)
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label", set_in_kwargs=True
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)
    role: PropertyRef = PropertyRef("role")


@dataclass(frozen=True)
class GSuiteGroupToGroupMemberRel(CartographyRelSchema):
    """
    MatchLink relationship from GSuite parent group to member group
    """

    target_node_label: str = "GSuiteGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("subgroup_id"),
        }
    )
    source_node_label: str = "GSuiteGroup"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {
            "id": PropertyRef("parent_group_id"),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "MEMBER_GSUITE_GROUP"
    properties: GSuiteGroupToGroupMemberRelProperties = (
        GSuiteGroupToGroupMemberRelProperties()
    )


@dataclass(frozen=True)
class GSuiteGroupToGroupOwnerRelProperties(CartographyRelProperties):
    """
    Properties for GSuite group to group owner relationship (MatchLink)
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label", set_in_kwargs=True
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)
    role: PropertyRef = PropertyRef("role")


@dataclass(frozen=True)
class GSuiteGroupToGroupOwnerRel(CartographyRelSchema):
    """
    MatchLink relationship from GSuite parent group to owner group
    """

    target_node_label: str = "GSuiteGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("subgroup_id"),
        }
    )
    source_node_label: str = "GSuiteGroup"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {
            "id": PropertyRef("parent_group_id"),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "OWNER_GSUITE_GROUP"
    properties: GSuiteGroupToGroupOwnerRelProperties = (
        GSuiteGroupToGroupOwnerRelProperties()
    )
