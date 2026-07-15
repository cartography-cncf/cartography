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
    id: PropertyRef = PropertyRef("id", description="Unique GSuite group ID.")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last update.",
    )

    # Group identifiers and basic info
    group_id: PropertyRef = PropertyRef(
        "id", description="Alias of the unique GSuite group ID."
    )
    email: PropertyRef = PropertyRef(
        "email", extra_index=True, description="Email address of the group."
    )
    name: PropertyRef = PropertyRef("name", description="Display name of the group.")
    description: PropertyRef = PropertyRef(
        "description", description="Description of the group."
    )

    # Group settings
    admin_created: PropertyRef = PropertyRef(
        "adminCreated",
        description="Whether an administrator created the group.",
    )
    direct_members_count: PropertyRef = PropertyRef(
        "directMembersCount", description="Number of direct group members."
    )

    # Metadata
    etag: PropertyRef = PropertyRef("etag", description="API resource ETag.")
    kind: PropertyRef = PropertyRef("kind", description="API resource type.")

    # Tenant relationship
    customer_id: PropertyRef = PropertyRef(
        "CUSTOMER_ID",
        set_in_kwargs=True,
        description="ID of the GSuite tenant that contains the group.",
    )


@dataclass(frozen=True)
class GSuiteGroupToTenantRelProperties(CartographyRelProperties):
    """
    Properties for GSuite group to tenant relationship
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GSuiteGroupToTenantRel(CartographyRelSchema):
    """A GSuite tenant contains a group."""

    target_node_label: str = "GSuiteTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("CUSTOMER_ID", set_in_kwargs=True),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GSuiteGroupToTenantRelProperties = GSuiteGroupToTenantRelProperties()


@dataclass(frozen=True)
class GSuiteGroupToMemberRelProperties(CartographyRelProperties):
    """
    Properties for GSuite group to member relationship
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# DEPRECATED: replaced by the canonical (:UserAccount)-[:MEMBER_OF]->(:UserGroup)
# edge (GSuiteGroupToMemberMemberOfRel). Kept for backward compatibility, will be
# removed in v1.0.0.
class GSuiteGroupToMemberRel(CartographyRelSchema):
    """Deprecated compatibility edge linking a user to a GSuite group."""

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
class GSuiteGroupToMemberMemberOfRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# Canonical ontology edge: (:UserAccount)-[:MEMBER_OF]->(:UserGroup)
class GSuiteGroupToMemberMemberOfRel(CartographyRelSchema):
    """A GSuite user account is a member of a GSuite group."""

    target_node_label: str = "GSuiteUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("member_ids", one_to_many=True),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "MEMBER_OF"
    properties: GSuiteGroupToMemberMemberOfRelProperties = (
        GSuiteGroupToMemberMemberOfRelProperties()
    )


@dataclass(frozen=True)
class GSuiteGroupToOwnerRelProperties(CartographyRelProperties):
    """
    Properties for GSuite group to owner relationship
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GSuiteGroupToOwnerRel(CartographyRelSchema):
    """A GSuite user account owns a GSuite group."""

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
    """A GSuite group with the canonical UserGroup label."""

    label: str = "GSuiteGroup"
    properties: GSuiteGroupNodeProperties = GSuiteGroupNodeProperties()
    sub_resource_relationship: GSuiteGroupToTenantRel = GSuiteGroupToTenantRel()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["GCPPrincipal", "UserGroup"])
    other_relationships = OtherRelationships(
        [
            GSuiteGroupToMemberRel(),
            GSuiteGroupToMemberMemberOfRel(),
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
# DEPRECATED: replaced by the canonical (:UserGroup)-[:MEMBER_OF]->(:UserGroup)
# edge (GSuiteGroupToGroupMemberMemberOfRel). Kept for backward compatibility,
# will be removed in v1.0.0.
class GSuiteGroupToGroupMemberRel(CartographyRelSchema):
    """Deprecated compatibility edge linking a member group to its parent group."""

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
# Canonical ontology edge: (:UserGroup)-[:MEMBER_OF]->(:UserGroup)
class GSuiteGroupToGroupMemberMemberOfRel(CartographyRelSchema):
    """A GSuite group is a member of another GSuite group."""

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
    rel_label: str = "MEMBER_OF"
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
    """A GSuite group owns another GSuite group."""

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
