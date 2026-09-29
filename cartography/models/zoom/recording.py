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
class ZoomRecordingNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Account-scoped recorded meeting occurrence UUID."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    account_id: PropertyRef = PropertyRef(
        "ACCOUNT_ID",
        set_in_kwargs=True,
        extra_index=True,
        description="Owning Zoom account ID.",
    )
    meeting_uuid: PropertyRef = PropertyRef(
        "meeting_uuid",
        description="Identifies this recorded meeting instance, including recurring meetings.",
    )
    meeting_id: PropertyRef = PropertyRef(
        "meeting_id",
        description="Provider meeting ID (meeting number), stored as a string.",
    )
    host_id: PropertyRef = PropertyRef(
        "host_id",
        extra_index=True,
        description="Provider user ID of the recorded meeting host.",
    )
    topic: PropertyRef = PropertyRef(
        "topic", description="Topic of the recorded meeting."
    )
    start_time: PropertyRef = PropertyRef(
        "start_time",
        description="Recorded meeting start_time as a native datetime, when available.",
    )
    duration: PropertyRef = PropertyRef(
        "duration", description="Recorded meeting duration in minutes."
    )
    total_size: PropertyRef = PropertyRef(
        "total_size", description="Aggregate recording size in bytes."
    )
    recording_count: PropertyRef = PropertyRef(
        "recording_count",
        description="Provider recording_count for this meeting instance.",
    )
    file_types: PropertyRef = PropertyRef(
        "file_types",
        description="Types of available recording files; file contents and access URLs are never fetched.",
    )
    password_protected: PropertyRef = PropertyRef(
        "password_protected",
        description="Whether settings supplies a nonempty passcode; unknown if omitted. Passcodes are never stored.",
    )
    share_recording: PropertyRef = PropertyRef(
        "share_recording",
        description="Provider sharing mode: publicly, internally, or none. Public sharing can still require authentication or a passcode.",
    )
    recording_authentication: PropertyRef = PropertyRef(
        "recording_authentication",
        description="Whether settings.recording_authentication restricts viewing to authenticated users.",
    )
    authentication_domains: PropertyRef = PropertyRef(
        "authentication_domains",
        description="Allowed viewer domains from settings.authentication_domains, when returned.",
    )
    on_demand: PropertyRef = PropertyRef(
        "on_demand", description="Whether viewing requires registration."
    )
    approval_type: PropertyRef = PropertyRef(
        "approval_type",
        description="Registration: 0 automatic approval, 1 manual approval, 2 not required.",
    )
    viewer_download: PropertyRef = PropertyRef(
        "viewer_download",
        description="Whether settings.viewer_download permits recording downloads.",
    )
    auto_delete: PropertyRef = PropertyRef(
        "auto_delete",
        description="Whether settings.auto_delete enables automatic deletion.",
    )
    auto_delete_date: PropertyRef = PropertyRef(
        "auto_delete_date",
        description="Provider settings.auto_delete_date, when automatic deletion is configured.",
    )


@dataclass(frozen=True)
class ZoomRecordingToHostRel(CartographyRelSchema):
    target_node_label: str = "ZoomUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("host_graph_id")}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HOSTED_BY"
    properties: ZoomResourceRelProperties = ZoomResourceRelProperties()


@dataclass(frozen=True)
class ZoomRecordingToMeetingRel(CartographyRelSchema):
    target_node_label: str = "ZoomMeeting"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("meeting_graph_id")}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "RECORDED_FROM"
    properties: ZoomResourceRelProperties = ZoomResourceRelProperties()


@dataclass(frozen=True)
class ZoomRecordingSchema(CartographyNodeSchema):
    """Cloud recording metadata for one meeting instance within the configured window.

    Contains aggregate file metadata and sharing configuration, never recordings,
    transcripts, passcodes, or URLs. Links to a scheduled meeting when it is ingested.
    Successful owner syncs expire records outside the rolling lookback window.
    """

    label: str = "ZoomRecording"
    properties: ZoomRecordingNodeProperties = ZoomRecordingNodeProperties()
    sub_resource_relationship: ZoomAccountResourceRel = ZoomAccountResourceRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [ZoomRecordingToHostRel(), ZoomRecordingToMeetingRel()]
    )
