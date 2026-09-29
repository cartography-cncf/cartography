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
class ZoomActivityEventProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    account_id: PropertyRef = PropertyRef(
        "ACCOUNT_ID", set_in_kwargs=True, extra_index=True
    )
    source: PropertyRef = PropertyRef(
        "source",
        description="Report API: signins, operations, or meeting_audit.",
        extra_index=True,
    )
    event_type: PropertyRef = PropertyRef(
        "event_type",
        description="Report type, action, or activity_category.",
        extra_index=True,
    )
    category: PropertyRef = PropertyRef(
        "category",
        description="Operations category_type, when returned.",
        extra_index=False,
    )
    occurred_at: PropertyRef = PropertyRef(
        "occurred_at",
        description="Report time or activity_time as a UTC native datetime.",
        extra_index=True,
    )
    operator_email: PropertyRef = PropertyRef(
        "operator_email",
        description="Normalized email from email, operator, or operator_email; unknown users have no user link.",
        extra_index=True,
    )
    client_type: PropertyRef = PropertyRef(
        "client_type", description="Sign-in report client_type.", extra_index=False
    )
    client_version: PropertyRef = PropertyRef(
        "client_version", description="Sign-in report version.", extra_index=True
    )


@dataclass(frozen=True)
class ZoomActivityUserRel(CartographyRelSchema):
    """PERFORMED_BY relationship to ZoomUser."""

    target_node_label: str = "ZoomUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("user_node_id", one_to_many=False)}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "PERFORMED_BY"
    properties: ZoomResourceRelProperties = ZoomResourceRelProperties()


@dataclass(frozen=True)
class ZoomActivityMeetingRel(CartographyRelSchema):
    """IN_MEETING relationship to ZoomMeeting."""

    target_node_label: str = "ZoomMeeting"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("meeting_node_id", one_to_many=False)}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "IN_MEETING"
    properties: ZoomResourceRelProperties = ZoomResourceRelProperties()


@dataclass(frozen=True)
class ZoomActivityEventSchema(CartographyNodeSchema):
    """A deduplicated sign-in, operation, or meeting-audit event within the configured UTC lookback window. Free-form event details are not retained."""

    label: str = "ZoomActivityEvent"
    properties: ZoomActivityEventProperties = ZoomActivityEventProperties()
    sub_resource_relationship: ZoomAccountResourceRel = ZoomAccountResourceRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [ZoomActivityUserRel(), ZoomActivityMeetingRel()]
    )
