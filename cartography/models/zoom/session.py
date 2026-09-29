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
class ZoomMeetingSessionProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Account-scoped meeting occurrence UUID."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    account_id: PropertyRef = PropertyRef(
        "ACCOUNT_ID",
        set_in_kwargs=True,
        extra_index=True,
        description="Owning Zoom account ID.",
    )
    uuid: PropertyRef = PropertyRef(
        "uuid",
        description="Dashboard meeting uuid identifies this occurrence.",
        extra_index=False,
    )
    meeting_id: PropertyRef = PropertyRef(
        "meeting_id",
        description="Dashboard meeting id (meeting number).",
        extra_index=True,
    )
    start_time: PropertyRef = PropertyRef(
        "start_time",
        description="Dashboard start_time as native datetime.",
        extra_index=True,
    )
    end_time: PropertyRef = PropertyRef(
        "end_time",
        description="Dashboard end_time as native datetime.",
        extra_index=False,
    )
    participant_count: PropertyRef = PropertyRef(
        "participant_count",
        description="Dashboard participants count.",
        extra_index=False,
    )
    has_recording: PropertyRef = PropertyRef(
        "has_recording", description="Dashboard has_recording.", extra_index=False
    )
    has_external_participant: PropertyRef = PropertyRef(
        "has_external_participant",
        description="Dashboard has_external_participant, when available.",
        extra_index=True,
    )


@dataclass(frozen=True)
class ZoomSessionMeetingRel(CartographyRelSchema):
    """INSTANCE_OF relationship to ZoomMeeting."""

    target_node_label: str = "ZoomMeeting"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("meeting_node_id", one_to_many=False)}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "INSTANCE_OF"
    properties: ZoomResourceRelProperties = ZoomResourceRelProperties()


@dataclass(frozen=True)
class ZoomSessionHostRel(CartographyRelSchema):
    """HOSTED_BY relationship to ZoomUser."""

    target_node_label: str = "ZoomUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("host_node_id", one_to_many=False)}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HOSTED_BY"
    properties: ZoomResourceRelProperties = ZoomResourceRelProperties()


@dataclass(frozen=True)
class ZoomMeetingSessionSchema(CartographyNodeSchema):
    """A past meeting instance observed by the Business dashboard within the configured UTC lookback window, including single-participant meetings."""

    label: str = "ZoomMeetingSession"
    properties: ZoomMeetingSessionProperties = ZoomMeetingSessionProperties()
    sub_resource_relationship: ZoomAccountResourceRel = ZoomAccountResourceRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [ZoomSessionMeetingRel(), ZoomSessionHostRel()]
    )
