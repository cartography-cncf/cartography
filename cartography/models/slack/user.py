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
class SlackUserNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef('id')
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)
    name: PropertyRef = PropertyRef('name', extra_index=True)
    real_name: PropertyRef = PropertyRef('real_name')
    display_name: PropertyRef = PropertyRef('profile.display_name')
    first_name: PropertyRef = PropertyRef('profile.first_name')
    last_name: PropertyRef = PropertyRef('profile.last_name')
    profile_title: PropertyRef = PropertyRef('profile.title')
    profile_phone: PropertyRef = PropertyRef('profile.phone')
    email: PropertyRef = PropertyRef('profile.email', extra_index=True)
    deleted: PropertyRef = PropertyRef('deleted')
    is_admin: PropertyRef = PropertyRef('is_admin')
    is_owner: PropertyRef = PropertyRef('is_owner')
    is_restricted: PropertyRef = PropertyRef('is_restricted')
    is_ultra_restricted: PropertyRef = PropertyRef('is_ultra_restricted')
    is_bot: PropertyRef = PropertyRef('is_bot')
    is_app_user: PropertyRef = PropertyRef('is_app_user')
    is_email_confirmed: PropertyRef = PropertyRef('is_email_confirmed')
    team: PropertyRef = PropertyRef('profile.team')


@dataclass(frozen=True)
class SlackUserToHumanRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
# (:SlackUser)<-[:IDENTITY_SLACK]-(:Human)
class SlackHumanToUserRel(CartographyRelSchema):
    target_node_label: str = 'Human'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'email': PropertyRef('profile.email')},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "IDENTITY_SLACK"
    properties: SlackUserToHumanRelProperties = SlackUserToHumanRelProperties()


@dataclass(frozen=True)
class SlackTeamToSlackUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
# (:SlackTeam)<-[:RESOURCE]-(:SlackUser)
class SlackTeamToUserRel(CartographyRelSchema):
    target_node_label: str = 'SlackTeam'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('TEAM_ID', set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "RESOURCE"
    properties: SlackTeamToSlackUserRelProperties = SlackTeamToSlackUserRelProperties()


@dataclass(frozen=True)
class SlackUserSchema(CartographyNodeSchema):
    label: str = 'SlackUser'
    properties: SlackUserNodeProperties = SlackUserNodeProperties()
    other_relationships: OtherRelationships = OtherRelationships(rels=[SlackHumanToUserRel()])
    sub_resource_relationship: SlackTeamToUserRel = SlackTeamToUserRel()
