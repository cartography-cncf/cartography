from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_source_node_matcher
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import SourceNodeMatcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class TailscaleGrantNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Stable content-hash ID (eg. `grant:a1b2c3d4e5f6`). Computed from the grant's src, dst, ip, app, and srcPosture fields.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated.",
    )
    sources: PropertyRef = PropertyRef(
        "sources", description="Native list of source selectors (users, groups, tags)."
    )
    destinations: PropertyRef = PropertyRef(
        "destinations",
        description="Native list of destination selectors (tags, groups, services, IPs).",
    )
    ip_rules: PropertyRef = PropertyRef(
        "ip_rules",
        description='Native list of network capabilities (eg. `["tcp:443"]`).',
    )
    app_capabilities: PropertyRef = PropertyRef(
        "app_capabilities",
        description="JSON-serialized dict of application capabilities.",
    )
    src_posture: PropertyRef = PropertyRef(
        "src_posture",
        description="Native list of required posture policies for sources.",
    )


@dataclass(frozen=True)
class TailscaleGrantToTailnetRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last Cartography update.",
    )


@dataclass(frozen=True)
# (:TailscaleTailnet)-[:RESOURCE]->(:TailscaleGrant)
class TailscaleGrantToTailnetRel(CartographyRelSchema):
    """Defines the RESOURCE relationship to TailscaleTailnet nodes."""

    target_node_label: str = "TailscaleTailnet"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("org", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: TailscaleGrantToTailnetRelProperties = (
        TailscaleGrantToTailnetRelProperties()
    )


@dataclass(frozen=True)
class TailscaleGrantToSourceGroupRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last Cartography update.",
    )


@dataclass(frozen=True)
# (:TailscaleGroup)-[:SOURCE]->(:TailscaleGrant)
class TailscaleGrantToSourceGroupRel(CartographyRelSchema):
    """Defines the SOURCE relationship to TailscaleGroup nodes."""

    target_node_label: str = "TailscaleGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("source_groups", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "SOURCE"
    properties: TailscaleGrantToSourceGroupRelProperties = (
        TailscaleGrantToSourceGroupRelProperties()
    )


@dataclass(frozen=True)
class TailscaleGrantToSourceUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last Cartography update.",
    )


@dataclass(frozen=True)
# (:TailscaleUser)-[:SOURCE]->(:TailscaleGrant)
class TailscaleGrantToSourceUserRel(CartographyRelSchema):
    """Defines the SOURCE relationship to TailscaleUser nodes."""

    target_node_label: str = "TailscaleUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"login_name": PropertyRef("source_users", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "SOURCE"
    properties: TailscaleGrantToSourceUserRelProperties = (
        TailscaleGrantToSourceUserRelProperties()
    )


@dataclass(frozen=True)
class TailscaleGrantToDestinationTagRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last Cartography update.",
    )


@dataclass(frozen=True)
# (:TailscaleGrant)-[:DESTINATION]->(:TailscaleTag)
class TailscaleGrantToDestinationTagRel(CartographyRelSchema):
    """Defines the DESTINATION relationship to TailscaleTag nodes."""

    target_node_label: str = "TailscaleTag"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("destination_tags", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "DESTINATION"
    properties: TailscaleGrantToDestinationTagRelProperties = (
        TailscaleGrantToDestinationTagRelProperties()
    )


@dataclass(frozen=True)
class TailscaleGrantToDestinationGroupRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last Cartography update.",
    )


@dataclass(frozen=True)
# (:TailscaleGrant)-[:DESTINATION]->(:TailscaleGroup)
class TailscaleGrantToDestinationGroupRel(CartographyRelSchema):
    """Defines the DESTINATION relationship to TailscaleGroup nodes."""

    target_node_label: str = "TailscaleGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("destination_groups", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "DESTINATION"
    properties: TailscaleGrantToDestinationGroupRelProperties = (
        TailscaleGrantToDestinationGroupRelProperties()
    )


@dataclass(frozen=True)
class TailscaleGrantSchema(CartographyNodeSchema):
    """
    A grant rule from the Tailscale ACL/policy file. Grants define access rules with
    sources, destinations, and capabilities.
    """

    label: str = "TailscaleGrant"
    properties: TailscaleGrantNodeProperties = TailscaleGrantNodeProperties()
    sub_resource_relationship: TailscaleGrantToTailnetRel = TailscaleGrantToTailnetRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            TailscaleGrantToSourceGroupRel(),
            TailscaleGrantToSourceUserRel(),
            TailscaleGrantToDestinationTagRel(),
            TailscaleGrantToDestinationGroupRel(),
        ],
    )


# MatchLink schemas for resolved effective access relationships.
# These connect users/groups to devices via grants.


@dataclass(frozen=True)
class TailscaleGrantAccessRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last Cartography update.",
    )
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label",
        set_in_kwargs=True,
        description="Label used to scope relationship cleanup.",
    )
    _sub_resource_id: PropertyRef = PropertyRef(
        "_sub_resource_id",
        set_in_kwargs=True,
        description="Identifier used to scope relationship cleanup.",
    )
    granted_by: PropertyRef = PropertyRef(
        "granted_by", description="Grant IDs that justify the resolved access."
    )


@dataclass(frozen=True)
class TailscaleUserToDeviceAccessMatchLink(CartographyRelSchema):
    """Indicates that a Tailscale user has effective access to a device through a grant."""

    source_node_label: str = "TailscaleUser"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"login_name": PropertyRef("user_login_name")},
    )
    target_node_label: str = "TailscaleDevice"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("device_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "CAN_ACCESS"
    properties: TailscaleGrantAccessRelProperties = TailscaleGrantAccessRelProperties()


@dataclass(frozen=True)
class TailscaleGroupToDeviceAccessMatchLink(CartographyRelSchema):
    """Indicates that a Tailscale group has effective access to a device through a grant."""

    source_node_label: str = "TailscaleGroup"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("group_id")},
    )
    target_node_label: str = "TailscaleDevice"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("device_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "CAN_ACCESS"
    properties: TailscaleGrantAccessRelProperties = TailscaleGrantAccessRelProperties()


@dataclass(frozen=True)
class TailscaleDeviceToDeviceAccessMatchLink(CartographyRelSchema):
    """Indicates that a tagged Tailscale device has effective access to another device through a grant."""

    source_node_label: str = "TailscaleDevice"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("source_device_id")},
    )
    target_node_label: str = "TailscaleDevice"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("device_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "CAN_ACCESS"
    properties: TailscaleGrantAccessRelProperties = TailscaleGrantAccessRelProperties()


@dataclass(frozen=True)
class TailscaleUserToServiceAccessMatchLink(CartographyRelSchema):
    """Indicates that a Tailscale user has effective access to a service through a grant."""

    source_node_label: str = "TailscaleUser"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"login_name": PropertyRef("user_login_name")},
    )
    target_node_label: str = "TailscaleService"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("service_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "CAN_ACCESS"
    properties: TailscaleGrantAccessRelProperties = TailscaleGrantAccessRelProperties()


@dataclass(frozen=True)
class TailscaleGroupToServiceAccessMatchLink(CartographyRelSchema):
    """Indicates that a Tailscale group has effective access to a service through a grant."""

    source_node_label: str = "TailscaleGroup"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("group_id")},
    )
    target_node_label: str = "TailscaleService"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("service_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "CAN_ACCESS"
    properties: TailscaleGrantAccessRelProperties = TailscaleGrantAccessRelProperties()
