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
class SlackGroupNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    description: PropertyRef = PropertyRef("description")
    is_subteam: PropertyRef = PropertyRef("is_subteam")
    handle: PropertyRef = PropertyRef("handle")
    is_external: PropertyRef = PropertyRef("is_external")
    date_create: PropertyRef = PropertyRef("date_create")
    date_update: PropertyRef = PropertyRef("date_update")
    date_delete: PropertyRef = PropertyRef("date_delete")
    created_by: PropertyRef = PropertyRef("created_by")
    updated_by: PropertyRef = PropertyRef("updated_by")
    user_count: PropertyRef = PropertyRef("user_count")
    channel_count: PropertyRef = PropertyRef("channel_count")


@dataclass(frozen=True)
class SlackGroupToSlackUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SlackUser)-[:MEMBER_OF]->(:SlackGroup)
class SlackGroupToUserRel(CartographyRelSchema):
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
class SlackGroupSchema(CartographyNodeSchema):
    label: str = "SlackGroup"
    properties: SlackGroupNodeProperties = SlackGroupNodeProperties()
    other_relationships: OtherRelationships = OtherRelationships(
        rels=[
            SlackGroupToUserRel(),
            SlackGroupToChannelRel(),
            SlackGroupToCreatorRel(),
        ],
    )
    sub_resource_relationship: SlackGroupToSlackTeamRel = SlackGroupToSlackTeamRel()
