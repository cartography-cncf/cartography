from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher
from cartography.models.zoom.resource import ZoomAccountResourceRel
from cartography.models.zoom.resource import ZoomResourceRelProperties


@dataclass(frozen=True)
class ZoomMeetingParticipantProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Account-scoped meeting instance and fingerprint of participant join identifiers.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    account_id: PropertyRef = PropertyRef(
        "ACCOUNT_ID",
        set_in_kwargs=True,
        extra_index=True,
        description="Owning Zoom account ID.",
    )
    session_id: PropertyRef = PropertyRef(
        "session_id",
        description="Account-scoped ZoomMeetingSession id.",
        extra_index=True,
    )
    participant_user_id: PropertyRef = PropertyRef(
        "participant_user_id",
        description="Dashboard participant_user_id identifies an authenticated Zoom user when available.",
        extra_index=False,
    )
    device: PropertyRef = PropertyRef(
        "device",
        description="Dashboard device category, such as Mac or Windows; not a device identifier.",
        extra_index=True,
    )
    client_version: PropertyRef = PropertyRef(
        "client_version",
        description="Dashboard version at the time of the meeting.",
        extra_index=True,
    )
    os: PropertyRef = PropertyRef(
        "os",
        description="Dashboard participant operating system at the time of the meeting.",
        extra_index=False,
    )
    os_version: PropertyRef = PropertyRef(
        "os_version",
        description="Dashboard participant operating system version at the time of the meeting.",
        extra_index=False,
    )
    join_time: PropertyRef = PropertyRef(
        "join_time",
        description="Dashboard join_time as native datetime.",
        extra_index=True,
    )
    leave_time: PropertyRef = PropertyRef(
        "leave_time",
        description="Dashboard leave_time as native datetime.",
        extra_index=False,
    )
    role: PropertyRef = PropertyRef(
        "role", description="Dashboard participant role.", extra_index=False
    )


@dataclass(frozen=True)
class ZoomParticipantSessionRel(CartographyRelSchema):
    """IN_MEETING relationship to ZoomMeetingSession."""

    target_node_label: str = "ZoomMeetingSession"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("session_id", one_to_many=False)}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "IN_MEETING"
    properties: ZoomResourceRelProperties = ZoomResourceRelProperties()


@dataclass(frozen=True)
class ZoomParticipantUserRel(CartographyRelSchema):
    """IS_USER relationship to ZoomUser."""

    target_node_label: str = "ZoomUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("user_node_id", one_to_many=False)}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "IS_USER"
    properties: ZoomResourceRelProperties = ZoomResourceRelProperties()


@dataclass(frozen=True)
class ZoomMeetingParticipantSchema(CartographyNodeSchema):
    """A participant join observed in a past meeting, not a persistent device. External and unauthenticated participants may lack identity or client information."""

    label: str = "ZoomMeetingParticipant"
    properties: ZoomMeetingParticipantProperties = ZoomMeetingParticipantProperties()
    sub_resource_relationship: ZoomAccountResourceRel = ZoomAccountResourceRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [ZoomParticipantSessionRel(), ZoomParticipantUserRel()]
    )
