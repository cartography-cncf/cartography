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
class ZoomGroupProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    account_id: PropertyRef = PropertyRef(
        "ACCOUNT_ID", set_in_kwargs=True, extra_index=True
    )
    zoom_id: PropertyRef = PropertyRef(
        "zoom_id", description="Group id.", extra_index=False
    )
    name: PropertyRef = PropertyRef("name", description="Group name.", extra_index=True)
    total_members: PropertyRef = PropertyRef(
        "total_members", description="Provider total_members.", extra_index=False
    )


@dataclass(frozen=True)
class ZoomGroupMemberRel(CartographyRelSchema):
    """MEMBER_OF relationship to ZoomUser."""

    target_node_label: str = "ZoomUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("member_ids", one_to_many=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "MEMBER_OF"
    properties: ZoomResourceRelProperties = ZoomResourceRelProperties()


@dataclass(frozen=True)
class ZoomGroupSchema(CartographyNodeSchema):
    """A Zoom account group with members correlated from the complete Users API snapshot."""

    label: str = "ZoomGroup"
    properties: ZoomGroupProperties = ZoomGroupProperties()
    sub_resource_relationship: ZoomAccountResourceRel = ZoomAccountResourceRel()
    other_relationships: OtherRelationships = OtherRelationships([ZoomGroupMemberRel()])
