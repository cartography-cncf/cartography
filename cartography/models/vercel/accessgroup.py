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


@dataclass(frozen=True)
class VercelAccessGroupNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("accessGroupId")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    created_at: PropertyRef = PropertyRef("createdAt")
    updated_at: PropertyRef = PropertyRef("updatedAt")
    members_count: PropertyRef = PropertyRef("membersCount")
    projects_count: PropertyRef = PropertyRef("projectsCount")
    is_dsync_managed: PropertyRef = PropertyRef("isDsyncManaged")
    member_ids: PropertyRef = PropertyRef("member_ids")
    project_ids: PropertyRef = PropertyRef("project_ids")


@dataclass(frozen=True)
class VercelAccessGroupToTeamRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:VercelTeam)-[:RESOURCE]->(:VercelAccessGroup)
class VercelAccessGroupToTeamRel(CartographyRelSchema):
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


@dataclass(frozen=True)
# (:VercelAccessGroup)-[:HAS_ACCESS_TO]->(:VercelProject)
class VercelAccessGroupToProjectRel(CartographyRelSchema):
    target_node_label: str = "VercelProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("project_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_ACCESS_TO"
    properties: VercelAccessGroupToProjectRelProperties = (
        VercelAccessGroupToProjectRelProperties()
    )


@dataclass(frozen=True)
class VercelAccessGroupSchema(CartographyNodeSchema):
    label: str = "VercelAccessGroup"
    properties: VercelAccessGroupNodeProperties = VercelAccessGroupNodeProperties()
    sub_resource_relationship: VercelAccessGroupToTeamRel = VercelAccessGroupToTeamRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [VercelAccessGroupToUserRel(), VercelAccessGroupToProjectRel()],
    )
