from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class VercelUserNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("uid")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    email: PropertyRef = PropertyRef("email", extra_index=True)
    username: PropertyRef = PropertyRef("username", extra_index=True)
    name: PropertyRef = PropertyRef("name")
    role: PropertyRef = PropertyRef("role")
    created_at: PropertyRef = PropertyRef("createdAt")
    joined_from: PropertyRef = PropertyRef("joinedFrom")
    confirmed: PropertyRef = PropertyRef("confirmed")


@dataclass(frozen=True)
class VercelUserToTeamResourceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:VercelTeam)-[:RESOURCE]->(:VercelUser)
class VercelUserToTeamResourceRel(CartographyRelSchema):
    target_node_label: str = "VercelTeam"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TEAM_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: VercelUserToTeamResourceRelProperties = (
        VercelUserToTeamResourceRelProperties()
    )


@dataclass(frozen=True)
class VercelUserToTeamMemberRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    role: PropertyRef = PropertyRef("role")
    confirmed: PropertyRef = PropertyRef("confirmed")
    joined_from: PropertyRef = PropertyRef("joinedFrom")


@dataclass(frozen=True)
# (:VercelUser)-[:MEMBER_OF]->(:VercelTeam)
class VercelUserToTeamMemberRel(CartographyRelSchema):
    target_node_label: str = "VercelTeam"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TEAM_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MEMBER_OF"
    properties: VercelUserToTeamMemberRelProperties = (
        VercelUserToTeamMemberRelProperties()
    )


@dataclass(frozen=True)
class VercelUserSchema(CartographyNodeSchema):
    label: str = "VercelUser"
    properties: VercelUserNodeProperties = VercelUserNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["UserAccount"])
    sub_resource_relationship: VercelUserToTeamResourceRel = (
        VercelUserToTeamResourceRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [VercelUserToTeamMemberRel()],
    )
