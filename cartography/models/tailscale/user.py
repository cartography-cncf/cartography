from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class TailscaleUserNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    display_name: PropertyRef = PropertyRef("displayName")
    login_name: PropertyRef = PropertyRef("loginName")
    profile_pic_url: PropertyRef = PropertyRef("profilePicUrl")
    tailnet_id: PropertyRef = PropertyRef("tailnetId")
    created: PropertyRef = PropertyRef("created")
    type: PropertyRef = PropertyRef("type")
    role: PropertyRef = PropertyRef("role")
    status: PropertyRef = PropertyRef("status")
    device_count: PropertyRef = PropertyRef("deviceCount")
    last_seen: PropertyRef = PropertyRef("lastSeen")
    currently_connected: PropertyRef = PropertyRef("currentlyConnected")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class TailscaleUserSchema(CartographyNodeSchema):
    label: str = "TailscaleUser"
    properties: TailscaleUserNodeProperties = TailscaleUserNodeProperties()
