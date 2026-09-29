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
class ZoomMeetingNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    account_id: PropertyRef = PropertyRef(
        "ACCOUNT_ID", set_in_kwargs=True, extra_index=True
    )
    meeting_id: PropertyRef = PropertyRef("meeting_id")
    host_id: PropertyRef = PropertyRef("host_id", extra_index=True)
    topic: PropertyRef = PropertyRef("topic")
    type: PropertyRef = PropertyRef("type")
    status: PropertyRef = PropertyRef("status")
    start_time: PropertyRef = PropertyRef("start_time")
    created_at: PropertyRef = PropertyRef("created_at")
    duration: PropertyRef = PropertyRef(
        "duration", description="Scheduled duration in minutes."
    )
    password_protected: PropertyRef = PropertyRef(
        "password_protected",
        description="Whether the response supplies a nonempty passcode; unknown if omitted. Passcodes are never stored.",
    )
    waiting_room: PropertyRef = PropertyRef("waiting_room")
    meeting_authentication: PropertyRef = PropertyRef("meeting_authentication")
    authentication_domains: PropertyRef = PropertyRef("authentication_domains")
    join_before_host: PropertyRef = PropertyRef("join_before_host")
    approval_type: PropertyRef = PropertyRef(
        "approval_type",
        description="Registration: 0 automatic approval, 1 manual approval, 2 not required.",
    )
    encryption_type: PropertyRef = PropertyRef("encryption_type")
    auto_recording: PropertyRef = PropertyRef("auto_recording")


@dataclass(frozen=True)
class ZoomMeetingRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ZoomAccountToMeetingRel(CartographyRelSchema):
    target_node_label: str = "ZoomAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ZoomMeetingRelProperties = ZoomMeetingRelProperties()


@dataclass(frozen=True)
class ZoomMeetingToHostRel(CartographyRelSchema):
    target_node_label: str = "ZoomUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("host_graph_id")}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HOSTED_BY"
    properties: ZoomMeetingRelProperties = ZoomMeetingRelProperties()


@dataclass(frozen=True)
class ZoomMeetingSchema(CartographyNodeSchema):
    """An unexpired scheduled meeting, including a recurring meeting series.

    Protection settings describe provider configuration, not verified public access.
    Meeting passcodes, join/start URLs, agendas and invitees are never ingested.
    """

    label: str = "ZoomMeeting"
    properties: ZoomMeetingNodeProperties = ZoomMeetingNodeProperties()
    sub_resource_relationship: ZoomAccountToMeetingRel = ZoomAccountToMeetingRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [ZoomMeetingToHostRel()]
    )
