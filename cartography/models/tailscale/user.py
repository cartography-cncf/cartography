from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class TailscaleUserNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    display_name: PropertyRef = PropertyRef("displayName")
    login_name: PropertyRef = PropertyRef("loginName")
    email: PropertyRef = PropertyRef("loginName", extra_index=True)
    profile_pic_url: PropertyRef = PropertyRef("profilePicUrl")
    created: PropertyRef = PropertyRef("created")
    type: PropertyRef = PropertyRef("type")
    role: PropertyRef = PropertyRef("role")
    status: PropertyRef = PropertyRef("status")
    device_count: PropertyRef = PropertyRef("deviceCount")
    last_seen: PropertyRef = PropertyRef("lastSeen")
    currently_connected: PropertyRef = PropertyRef("currentlyConnected")


@dataclass(frozen=True)
class TailscaleUserToTailnetRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:TailscaleTailnet)-[:RESOURCE]->(:TailscaleUser)
class TailscaleUserToTailnetRel(CartographyRelSchema):
    target_node_label: str = "TailscaleTailnet"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("org", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: TailscaleUserToTailnetRelProperties = (
        TailscaleUserToTailnetRelProperties()
    )


@dataclass(frozen=True)
class TailscaleUserSchema(CartographyNodeSchema):
    label: str = "TailscaleUser"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        ["UserAccount"]
    )  # UserAccount label is used for ontology mapping
    properties: TailscaleUserNodeProperties = TailscaleUserNodeProperties()
    sub_resource_relationship: TailscaleUserToTailnetRel = TailscaleUserToTailnetRel()
