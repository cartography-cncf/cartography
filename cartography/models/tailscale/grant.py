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
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    sources: PropertyRef = PropertyRef("sources")
    destinations: PropertyRef = PropertyRef("destinations")
    ip_rules: PropertyRef = PropertyRef("ip_rules")
    app_capabilities: PropertyRef = PropertyRef("app_capabilities")
    src_posture: PropertyRef = PropertyRef("src_posture")


@dataclass(frozen=True)
class TailscaleGrantToTailnetRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:TailscaleTailnet)-[:RESOURCE]->(:TailscaleGrant)
class TailscaleGrantToTailnetRel(CartographyRelSchema):
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
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:TailscaleGroup)-[:SOURCE]->(:TailscaleGrant)
class TailscaleGrantToSourceGroupRel(CartographyRelSchema):
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
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:TailscaleUser)-[:SOURCE]->(:TailscaleGrant)
class TailscaleGrantToSourceUserRel(CartographyRelSchema):
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
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:TailscaleGrant)-[:DESTINATION]->(:TailscaleTag)
class TailscaleGrantToDestinationTagRel(CartographyRelSchema):
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
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:TailscaleGrant)-[:DESTINATION]->(:TailscaleGroup)
class TailscaleGrantToDestinationGroupRel(CartographyRelSchema):
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
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label",
        set_in_kwargs=True,
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)
    granted_by: PropertyRef = PropertyRef("granted_by")


@dataclass(frozen=True)
class TailscaleUserToDeviceAccessMatchLink(CartographyRelSchema):
    """MatchLink: (:TailscaleUser)-[:CAN_ACCESS]->(:TailscaleDevice)

    Represents resolved effective access from a user to a device via a grant.
    """

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
    """MatchLink: (:TailscaleGroup)-[:CAN_ACCESS]->(:TailscaleDevice)

    Represents resolved effective access from a group to a device via a grant.
    """

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
    """MatchLink: (:TailscaleDevice)-[:CAN_ACCESS]->(:TailscaleDevice)

    Represents resolved effective access from a tagged device (source) to
    another device (destination) via a grant where the source is a tag.
    """

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
    """MatchLink: (:TailscaleUser)-[:CAN_ACCESS]->(:TailscaleService)

    Represents resolved effective access from a user to a service via a grant.
    """

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
    """MatchLink: (:TailscaleGroup)-[:CAN_ACCESS]->(:TailscaleService)

    Represents resolved effective access from a group to a service via a grant.
    """

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
