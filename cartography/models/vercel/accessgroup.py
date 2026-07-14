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
class VercelAccessGroupNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("accessGroupId", description="Access group ID.")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated", set_in_kwargs=True, description="Timestamp of the last update."
    )
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Access group name."
    )
    created_at: PropertyRef = PropertyRef(
        "createdAt", description="Timestamp when the access group was created."
    )
    updated_at: PropertyRef = PropertyRef(
        "updatedAt", description="Timestamp when the access group was last updated."
    )
    members_count: PropertyRef = PropertyRef(
        "membersCount", description="Number of members in the access group."
    )
    projects_count: PropertyRef = PropertyRef(
        "projectsCount", description="Number of projects assigned to the access group."
    )
    is_dsync_managed: PropertyRef = PropertyRef(
        "isDsyncManaged", description="Whether directory sync manages the access group."
    )
    member_ids: PropertyRef = PropertyRef(
        "member_ids", description="IDs of users in the access group."
    )


@dataclass(frozen=True)
class VercelAccessGroupToTeamRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:VercelTeam)-[:RESOURCE]->(:VercelAccessGroup)
class VercelAccessGroupToTeamRel(CartographyRelSchema):
    """The Vercel team contains this access group as a resource."""

    target_node_label: str = "VercelTeam"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TEAM_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: VercelAccessGroupToTeamRelProperties = (
        VercelAccessGroupToTeamRelProperties()
    )


@dataclass(frozen=True)
class VercelAccessGroupToUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:VercelAccessGroup)-[:HAS_MEMBER]->(:VercelUser)
class VercelAccessGroupToUserRel(CartographyRelSchema):
    """The Vercel access group contains this user as a member."""

    target_node_label: str = "VercelUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("member_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_MEMBER"
    properties: VercelAccessGroupToUserRelProperties = (
        VercelAccessGroupToUserRelProperties()
    )


@dataclass(frozen=True)
class VercelAccessGroupToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label", set_in_kwargs=True
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)
    role: PropertyRef = PropertyRef("role")


@dataclass(frozen=True)
# (:VercelAccessGroup)-[:HAS_ACCESS_TO {role}]->(:VercelProject)
class VercelAccessGroupToProjectRel(CartographyRelSchema):
    """The Vercel access group grants role-based access to this project."""

    target_node_label: str = "VercelProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("projectId")},
    )
    source_node_label: str = "VercelAccessGroup"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("accessGroupId")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_ACCESS_TO"
    properties: VercelAccessGroupToProjectRelProperties = (
        VercelAccessGroupToProjectRelProperties()
    )


@dataclass(frozen=True)
class VercelAccessGroupSchema(CartographyNodeSchema):
    """A Vercel team access group with the canonical Group label."""

    label: str = "VercelAccessGroup"
    properties: VercelAccessGroupNodeProperties = VercelAccessGroupNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Group"])
    sub_resource_relationship: VercelAccessGroupToTeamRel = VercelAccessGroupToTeamRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [VercelAccessGroupToUserRel()],
    )
