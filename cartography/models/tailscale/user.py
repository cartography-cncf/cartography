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
    id: PropertyRef = PropertyRef(
        "id", description="The unique identifier for the user."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated.",
    )
    display_name: PropertyRef = PropertyRef(
        "displayName", description="The name of the user."
    )
    login_name: PropertyRef = PropertyRef(
        "loginName", description="The emailish login name of the user."
    )
    email: PropertyRef = PropertyRef(
        "loginName", extra_index=True, description="The email of the user."
    )
    profile_pic_url: PropertyRef = PropertyRef(
        "profilePicUrl", description="The profile pic URL for the user."
    )
    created: PropertyRef = PropertyRef(
        "created", description="The time the user joined their tailnet."
    )
    type: PropertyRef = PropertyRef(
        "type",
        description="The type of relation this user has to the tailnet associated with the request.",
    )
    role: PropertyRef = PropertyRef(
        "role", description="The role of the user. Learn more about user roles."
    )
    status: PropertyRef = PropertyRef("status", description="The status of the user.")
    device_count: PropertyRef = PropertyRef(
        "deviceCount", description="Number of devices the user owns."
    )
    last_seen: PropertyRef = PropertyRef(
        "lastSeen",
        description="The later of either: - The last time any of the user's nodes were connected to the network. - The last time the user authenticated to any tailscale service, including the admin panel.",
    )
    currently_connected: PropertyRef = PropertyRef(
        "currentlyConnected",
        description="`true` when the user has a node currently connected to the control server.",
    )


@dataclass(frozen=True)
class TailscaleUserToTailnetRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last Cartography update.",
    )


@dataclass(frozen=True)
# (:TailscaleTailnet)-[:RESOURCE]->(:TailscaleUser)
class TailscaleUserToTailnetRel(CartographyRelSchema):
    """Defines the RESOURCE relationship to TailscaleTailnet nodes."""

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
    """Representation of a user within a tailnet."""

    label: str = "TailscaleUser"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        ["UserAccount"]
    )  # UserAccount label is used for ontology mapping
    properties: TailscaleUserNodeProperties = TailscaleUserNodeProperties()
    sub_resource_relationship: TailscaleUserToTailnetRel = TailscaleUserToTailnetRel()
