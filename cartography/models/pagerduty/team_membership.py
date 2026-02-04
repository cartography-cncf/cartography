from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_source_node_matcher
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import SourceNodeMatcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class PagerDutyTeamMembershipRelProperties(CartographyRelProperties):
    # Mandatory fields for MatchLinks
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label", set_in_kwargs=True
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)

    # Business property: the role of the user in the team (e.g., "manager", "responder")
    role: PropertyRef = PropertyRef("role")


@dataclass(frozen=True)
class PagerDutyTeamMembershipMatchLink(CartographyRelSchema):
    """
    MatchLink for the MEMBER_OF relationship between PagerDutyUser and PagerDutyTeam.

    This uses MatchLinks because the relationship has a 'role' property that varies
    per user-team pair (e.g., "manager", "responder"), which is a rich relationship
    property scenario as described in the MatchLinks documentation.
    """

    rel_label: str = "MEMBER_OF"
    direction: LinkDirection = LinkDirection.OUTWARD
    properties: PagerDutyTeamMembershipRelProperties = (
        PagerDutyTeamMembershipRelProperties()
    )

    # Target node: PagerDutyTeam
    target_node_label: str = "PagerDutyTeam"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("team")},
    )

    # Source node: PagerDutyUser
    source_node_label: str = "PagerDutyUser"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("user")},
    )
