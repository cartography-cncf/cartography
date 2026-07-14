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
    id: PropertyRef = PropertyRef("uid", description="User ID.")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated", set_in_kwargs=True, description="Timestamp of the last update."
    )
    email: PropertyRef = PropertyRef(
        "email", extra_index=True, description="User email address."
    )
    username: PropertyRef = PropertyRef(
        "username", extra_index=True, description="Vercel username."
    )
    name: PropertyRef = PropertyRef("name", description="User display name.")
    role: PropertyRef = PropertyRef("role", description="User role in the team.")
    created_at: PropertyRef = PropertyRef(
        "createdAt", description="Timestamp when the user account was created."
    )
    joined_from: PropertyRef = PropertyRef(
        "joinedFrom", description="Method by which the user joined the team."
    )
    confirmed: PropertyRef = PropertyRef(
        "confirmed", description="Whether the team membership is confirmed."
    )


@dataclass(frozen=True)
class VercelUserToTeamResourceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:VercelTeam)-[:RESOURCE]->(:VercelUser)
class VercelUserToTeamResourceRel(CartographyRelSchema):
    """The Vercel team contains this user as a resource."""

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
    """The Vercel user belongs to this team with membership details."""

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
    """A Vercel team member with the canonical UserAccount label."""

    label: str = "VercelUser"
    properties: VercelUserNodeProperties = VercelUserNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["UserAccount"])
    sub_resource_relationship: VercelUserToTeamResourceRel = (
        VercelUserToTeamResourceRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [VercelUserToTeamMemberRel()],
    )
