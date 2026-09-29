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
class ZoomRecordingNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    account_id: PropertyRef = PropertyRef(
        "ACCOUNT_ID", set_in_kwargs=True, extra_index=True
    )
    meeting_uuid: PropertyRef = PropertyRef(
        "meeting_uuid",
        description="Identifies this recorded meeting instance, including recurring meetings.",
    )
    meeting_id: PropertyRef = PropertyRef("meeting_id")
    host_id: PropertyRef = PropertyRef("host_id", extra_index=True)
    topic: PropertyRef = PropertyRef("topic")
    start_time: PropertyRef = PropertyRef("start_time")
    duration: PropertyRef = PropertyRef(
        "duration", description="Recorded meeting duration in minutes."
    )
    total_size: PropertyRef = PropertyRef(
        "total_size", description="Aggregate recording size in bytes."
    )
    recording_count: PropertyRef = PropertyRef("recording_count")
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
    recording_authentication: PropertyRef = PropertyRef("recording_authentication")
    authentication_domains: PropertyRef = PropertyRef("authentication_domains")
    on_demand: PropertyRef = PropertyRef(
        "on_demand", description="Whether viewing requires registration."
    )
    approval_type: PropertyRef = PropertyRef(
        "approval_type",
        description="Registration: 0 automatic approval, 1 manual approval, 2 not required.",
    )
    viewer_download: PropertyRef = PropertyRef("viewer_download")
    auto_delete: PropertyRef = PropertyRef("auto_delete")
    auto_delete_date: PropertyRef = PropertyRef("auto_delete_date")


@dataclass(frozen=True)
class ZoomRecordingRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ZoomAccountToRecordingRel(CartographyRelSchema):
    target_node_label: str = "ZoomAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ZoomRecordingRelProperties = ZoomRecordingRelProperties()


@dataclass(frozen=True)
class ZoomRecordingToHostRel(CartographyRelSchema):
    target_node_label: str = "ZoomUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("host_graph_id")}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HOSTED_BY"
    properties: ZoomRecordingRelProperties = ZoomRecordingRelProperties()


@dataclass(frozen=True)
class ZoomRecordingToMeetingRel(CartographyRelSchema):
    target_node_label: str = "ZoomMeeting"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("meeting_graph_id")}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "RECORDED_FROM"
    properties: ZoomRecordingRelProperties = ZoomRecordingRelProperties()


@dataclass(frozen=True)
class ZoomRecordingSchema(CartographyNodeSchema):
    """Cloud recording metadata for one meeting instance within the configured window.

    Contains aggregate file metadata and sharing configuration, never recordings,
    transcripts, passcodes, or URLs. Links to a scheduled meeting when it is ingested.
    Successful owner syncs expire records outside the rolling lookback window.
    """

    label: str = "ZoomRecording"
    properties: ZoomRecordingNodeProperties = ZoomRecordingNodeProperties()
    sub_resource_relationship: ZoomAccountToRecordingRel = ZoomAccountToRecordingRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [ZoomRecordingToHostRel(), ZoomRecordingToMeetingRel()]
    )
