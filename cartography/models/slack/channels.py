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
class SlackChannelNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Slack channel ID.")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last update.",
    )
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Slack channel name."
    )
    is_private: PropertyRef = PropertyRef(
        "is_private", description="Whether the channel is private."
    )
    created: PropertyRef = PropertyRef(
        "created", description="Channel creation timestamp."
    )
    is_archived: PropertyRef = PropertyRef(
        "is_archived", description="Whether the channel is archived."
    )
    is_general: PropertyRef = PropertyRef(
        "is_general", description="Whether this is the workspace's general channel."
    )
    is_shared: PropertyRef = PropertyRef(
        "is_shared", description="Whether the channel is shared across workspaces."
    )
    is_org_shared: PropertyRef = PropertyRef(
        "is_org_shared",
        description="Whether the channel is shared across an organization.",
    )
    topic: PropertyRef = PropertyRef("topic.value", description="Channel topic.")
    purpose: PropertyRef = PropertyRef("purpose.value", description="Channel purpose.")
    num_members: PropertyRef = PropertyRef(
        "num_members", description="Number of channel members."
    )


@dataclass(frozen=True)
class SlackChannelToSlackUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SlackUser)-[:CREATED]->(:SlackChannel)
class SlackChannelToCreatorRel(CartographyRelSchema):
    """A SlackUser-labeled account created a channel."""

    target_node_label: str = "SlackUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("creator")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CREATED"
    properties: SlackChannelToSlackUserRelProperties = (
        SlackChannelToSlackUserRelProperties()
    )


@dataclass(frozen=True)
# (:SlackUser)-[:MEMBER_OF]->(:SlackChannel)
class SlackChannelToUserRel(CartographyRelSchema):
    """A SlackUser-labeled account is a member of a channel."""

    target_node_label: str = "SlackUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("member_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "MEMBER_OF"
    properties: SlackChannelToSlackUserRelProperties = (
        SlackChannelToSlackUserRelProperties()
    )


@dataclass(frozen=True)
class SlackTeamToSlackChannelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SlackTeam)-[:RESOURCE]->(:SlackChannel)
class SlackTeamToChannelRel(CartographyRelSchema):
    """A Slack workspace contains a channel."""

    target_node_label: str = "SlackTeam"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TEAM_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SlackTeamToSlackChannelRelProperties = (
        SlackTeamToSlackChannelRelProperties()
    )


@dataclass(frozen=True)
class SlackChannelToSlackBotRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SlackBot)-[:CREATED]->(:SlackChannel)
class SlackChannelToBotCreatorRel(CartographyRelSchema):
    """A Slack bot created a channel."""

    target_node_label: str = "SlackBot"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("creator")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CREATED"
    properties: SlackChannelToSlackBotRelProperties = (
        SlackChannelToSlackBotRelProperties()
    )


@dataclass(frozen=True)
# (:SlackBot)-[:MEMBER_OF]->(:SlackChannel)
class SlackChannelToBotRel(CartographyRelSchema):
    """A Slack bot is a member of a channel."""

    target_node_label: str = "SlackBot"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("member_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "MEMBER_OF"
    properties: SlackChannelToSlackBotRelProperties = (
        SlackChannelToSlackBotRelProperties()
    )


@dataclass(frozen=True)
class SlackChannelSchema(CartographyNodeSchema):
    """A channel in a Slack workspace."""

    label: str = "SlackChannel"
    properties: SlackChannelNodeProperties = SlackChannelNodeProperties()
    other_relationships: OtherRelationships = OtherRelationships(
        rels=[
            SlackChannelToUserRel(),
            SlackChannelToCreatorRel(),
            SlackChannelToBotRel(),
            SlackChannelToBotCreatorRel(),
        ],
    )
    sub_resource_relationship: SlackTeamToChannelRel = SlackTeamToChannelRel()
