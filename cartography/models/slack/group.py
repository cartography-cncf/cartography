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
class SlackGroupNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Slack user group ID.")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last update.",
    )
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Slack user group name."
    )
    description: PropertyRef = PropertyRef(
        "description", description="User group description."
    )
    is_subteam: PropertyRef = PropertyRef(
        "is_subteam", description="Whether this is a subteam."
    )
    handle: PropertyRef = PropertyRef(
        "handle", description="User group mention handle."
    )
    is_external: PropertyRef = PropertyRef(
        "is_external", description="Whether the user group is external."
    )
    date_create: PropertyRef = PropertyRef(
        "date_create", description="User group creation timestamp."
    )
    date_update: PropertyRef = PropertyRef(
        "date_update", description="User group update timestamp."
    )
    date_delete: PropertyRef = PropertyRef(
        "date_delete", description="User group deletion timestamp."
    )
    created_by: PropertyRef = PropertyRef(
        "created_by", description="ID of the account that created the user group."
    )
    updated_by: PropertyRef = PropertyRef(
        "updated_by", description="ID of the account that last updated the user group."
    )
    user_count: PropertyRef = PropertyRef(
        "user_count", description="Number of user group members."
    )
    channel_count: PropertyRef = PropertyRef(
        "channel_count", description="Number of channels linked to the user group."
    )


@dataclass(frozen=True)
class SlackGroupToSlackUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SlackUser)-[:MEMBER_OF]->(:SlackGroup)
class SlackGroupToUserRel(CartographyRelSchema):
    """A SlackUser-labeled account is a member of a user group."""

    target_node_label: str = "SlackUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("member_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "MEMBER_OF"
    properties: SlackGroupToSlackUserRelProperties = (
        SlackGroupToSlackUserRelProperties()
    )


@dataclass(frozen=True)
class SlackGroupToCreatorRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SlackUser)-[:CREATED]->(:SlackGroup)
class SlackGroupToCreatorRel(CartographyRelSchema):
    """A SlackUser-labeled account created a user group."""

    target_node_label: str = "SlackUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("created_by")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CREATED"
    properties: SlackGroupToCreatorRelProperties = SlackGroupToCreatorRelProperties()


@dataclass(frozen=True)
class SlackGroupToSlackTeamRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SlackTeam)-[:RESOURCE]->(:SlackGroup)
class SlackGroupToSlackTeamRel(CartographyRelSchema):
    """A Slack workspace contains a user group."""

    target_node_label: str = "SlackTeam"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TEAM_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SlackGroupToSlackTeamRelProperties = (
        SlackGroupToSlackTeamRelProperties()
    )


class SlackTeamToTeamRel(CartographyRelSchema):
    """An alternate schema for a Slack workspace containing a user group."""

    target_node_label: str = "SlackTeam"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TEAM_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SlackGroupToSlackTeamRelProperties = (
        SlackGroupToSlackTeamRelProperties()
    )


@dataclass(frozen=True)
class SlackGroupToSlackChannelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SlackChannel)<-[:MEMBER_OF]-(:SlackGroup)
class SlackGroupToChannelRel(CartographyRelSchema):
    """A Slack user group is a member of a channel."""

    target_node_label: str = "SlackChannel"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("channel_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MEMBER_OF"
    properties: SlackGroupToSlackChannelRelProperties = (
        SlackGroupToSlackChannelRelProperties()
    )


@dataclass(frozen=True)
class SlackGroupToSlackBotRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SlackBot)-[:MEMBER_OF]->(:SlackGroup)
class SlackGroupToBotRel(CartographyRelSchema):
    """A Slack bot is a member of a user group."""

    target_node_label: str = "SlackBot"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("member_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "MEMBER_OF"
    properties: SlackGroupToSlackBotRelProperties = SlackGroupToSlackBotRelProperties()


@dataclass(frozen=True)
# (:SlackBot)-[:CREATED]->(:SlackGroup)
class SlackGroupToBotCreatorRel(CartographyRelSchema):
    """A Slack bot created a user group."""

    target_node_label: str = "SlackBot"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("created_by")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CREATED"
    properties: SlackGroupToSlackBotRelProperties = SlackGroupToSlackBotRelProperties()


@dataclass(frozen=True)
class SlackGroupSchema(CartographyNodeSchema):
    """A Slack user group with the canonical UserGroup label."""

    label: str = "SlackGroup"
    properties: SlackGroupNodeProperties = SlackGroupNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["UserGroup"])
    other_relationships: OtherRelationships = OtherRelationships(
        rels=[
            SlackGroupToUserRel(),
            SlackGroupToChannelRel(),
            SlackGroupToCreatorRel(),
            SlackGroupToBotRel(),
            SlackGroupToBotCreatorRel(),
        ],
    )
    sub_resource_relationship: SlackGroupToSlackTeamRel = SlackGroupToSlackTeamRel()
