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
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    is_private: PropertyRef = PropertyRef("is_private")
    created: PropertyRef = PropertyRef("created")
    is_archived: PropertyRef = PropertyRef("is_archived")
    is_general: PropertyRef = PropertyRef("is_general")
    is_shared: PropertyRef = PropertyRef("is_shared")
    is_org_shared: PropertyRef = PropertyRef("is_org_shared")
    topic: PropertyRef = PropertyRef("topic.value")
    purpose: PropertyRef = PropertyRef("purpose.value")
    num_members: PropertyRef = PropertyRef("num_members")


@dataclass(frozen=True)
class SlackChannelToSlackUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SlackUser)-[:CREATED]->(:SlackChannel)
class SlackChannelToCreatorRel(CartographyRelSchema):
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
class SlackChannelSchema(CartographyNodeSchema):
    label: str = "SlackChannel"
    properties: SlackChannelNodeProperties = SlackChannelNodeProperties()
    other_relationships: OtherRelationships = OtherRelationships(
        rels=[
            SlackChannelToUserRel(),
            SlackChannelToCreatorRel(),
        ],
    )
    sub_resource_relationship: SlackTeamToChannelRel = SlackTeamToChannelRel()
