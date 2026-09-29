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
class ZoomMeetingNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Account-scoped Zoom meeting number."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    account_id: PropertyRef = PropertyRef(
        "ACCOUNT_ID",
        set_in_kwargs=True,
        extra_index=True,
        description="Owning Zoom account ID.",
    )
    meeting_id: PropertyRef = PropertyRef(
        "meeting_id",
        description="Provider meeting ID (meeting number), stored as a string.",
    )
    host_id: PropertyRef = PropertyRef(
        "host_id", extra_index=True, description="Provider user ID of the meeting host."
    )
    topic: PropertyRef = PropertyRef(
        "topic", description="Meeting topic from the meeting details response."
    )
    type: PropertyRef = PropertyRef(
        "type",
        description="Provider meeting type code for instant, scheduled, or recurring meetings.",
    )
    status: PropertyRef = PropertyRef(
        "status", description="Meeting status from the meeting details response."
    )
    start_time: PropertyRef = PropertyRef(
        "start_time",
        description="Scheduled start_time as a native datetime, when available.",
    )
    created_at: PropertyRef = PropertyRef(
        "created_at",
        description="Provider created_at as a native datetime, when available.",
    )
    duration: PropertyRef = PropertyRef(
        "duration", description="Scheduled duration in minutes."
    )
    password_protected: PropertyRef = PropertyRef(
        "password_protected",
        description="Whether the response supplies a nonempty passcode; unknown if omitted. Passcodes are never stored.",
    )
    waiting_room: PropertyRef = PropertyRef(
        "waiting_room",
        description="Whether settings.waiting_room enables the waiting room.",
    )
    meeting_authentication: PropertyRef = PropertyRef(
        "meeting_authentication",
        description="Whether settings.meeting_authentication requires authenticated participants.",
    )
    authentication_domains: PropertyRef = PropertyRef(
        "authentication_domains",
        description="Allowed domains from settings.authentication_domains, when returned.",
    )
    join_before_host: PropertyRef = PropertyRef(
        "join_before_host",
        description="Whether settings.join_before_host allows participants to join before the host.",
    )
    approval_type: PropertyRef = PropertyRef(
        "approval_type",
        description="Registration: 0 automatic approval, 1 manual approval, 2 not required.",
    )
    encryption_type: PropertyRef = PropertyRef(
        "encryption_type",
        description="Configured encryption mode from settings.encryption_type.",
    )
    auto_recording: PropertyRef = PropertyRef(
        "auto_recording",
        description="Configured automatic recording mode from settings.auto_recording.",
    )


@dataclass(frozen=True)
class ZoomMeetingToHostRel(CartographyRelSchema):
    target_node_label: str = "ZoomUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("host_graph_id")}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HOSTED_BY"
    properties: ZoomResourceRelProperties = ZoomResourceRelProperties()


@dataclass(frozen=True)
class ZoomMeetingSchema(CartographyNodeSchema):
    """An unexpired scheduled meeting, including a recurring meeting series.

    Protection settings describe provider configuration, not verified public access.
    Meeting passcodes, join/start URLs, agendas and invitees are never ingested.
    """

    label: str = "ZoomMeeting"
    properties: ZoomMeetingNodeProperties = ZoomMeetingNodeProperties()
    sub_resource_relationship: ZoomAccountResourceRel = ZoomAccountResourceRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [ZoomMeetingToHostRel()]
    )
