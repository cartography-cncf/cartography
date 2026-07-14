from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class SlackUserNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Slack user ID.")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last update.",
    )
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Slack username."
    )
    real_name: PropertyRef = PropertyRef("real_name", description="User's full name.")
    display_name: PropertyRef = PropertyRef(
        "profile.display_name", description="User's display name."
    )
    first_name: PropertyRef = PropertyRef(
        "profile.first_name", description="User's first name."
    )
    last_name: PropertyRef = PropertyRef(
        "profile.last_name", description="User's last name."
    )
    profile_title: PropertyRef = PropertyRef(
        "profile.title", description="User's profile title."
    )
    profile_phone: PropertyRef = PropertyRef(
        "profile.phone", description="User's profile phone number."
    )
    email: PropertyRef = PropertyRef(
        "profile.email", extra_index=True, description="User's email address."
    )
    deleted: PropertyRef = PropertyRef(
        "deleted", description="Whether the user is deleted."
    )
    is_admin: PropertyRef = PropertyRef(
        "is_admin", description="Whether the user is a workspace administrator."
    )
    is_owner: PropertyRef = PropertyRef(
        "is_owner", description="Whether the user is a workspace owner."
    )
    is_restricted: PropertyRef = PropertyRef(
        "is_restricted", description="Whether the user is a restricted guest."
    )
    is_ultra_restricted: PropertyRef = PropertyRef(
        "is_ultra_restricted",
        description="Whether the user is an ultra-restricted guest.",
    )
    is_email_confirmed: PropertyRef = PropertyRef(
        "is_email_confirmed", description="Whether the user's email is confirmed."
    )
    team: PropertyRef = PropertyRef(
        "profile.team", description="ID of the user's Slack workspace."
    )
    has_mfa: PropertyRef = PropertyRef(
        "has_mfa", description="Whether multi-factor authentication is enabled."
    )


@dataclass(frozen=True)
class SlackTeamToSlackUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SlackTeam)-[:RESOURCE]->(:SlackUser)
class SlackTeamToUserRel(CartographyRelSchema):
    """A Slack workspace contains a user account."""

    target_node_label: str = "SlackTeam"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TEAM_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SlackTeamToSlackUserRelProperties = SlackTeamToSlackUserRelProperties()


@dataclass(frozen=True)
class SlackUserSchema(CartographyNodeSchema):
    """A Slack user account with the canonical UserAccount label."""

    label: str = "SlackUser"
    properties: SlackUserNodeProperties = SlackUserNodeProperties()
    sub_resource_relationship: SlackTeamToUserRel = SlackTeamToUserRel()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["UserAccount"])
