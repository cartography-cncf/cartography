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
class TailscaleTagNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name")


@dataclass(frozen=True)
class TailscaleTagToTailnetRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:TailscaleTailnet)-[:RESOURCE]->(:TailscaleTag)
class TailscaleTagToTailnetRel(CartographyRelSchema):
    target_node_label: str = "TailscaleTailnet"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("org", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: TailscaleTagToTailnetRelProperties = (
        TailscaleTagToTailnetRelProperties()
    )


@dataclass(frozen=True)
class TailscaleTagToUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:TailscaleUser)-[:OWNS]->(:TailscaleTag)
class TailscaleTagToUserRel(CartographyRelSchema):
    target_node_label: str = "TailscaleUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"login_name": PropertyRef("owners", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "OWNS"
    properties: TailscaleTagToUserRelProperties = TailscaleTagToUserRelProperties()


@dataclass(frozen=True)
class TailscaleTagToGroupRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:TailscaleGroup)-[:OWNS]->(:TailscaleTag)
class TailscaleTagToGroupRel(CartographyRelSchema):
    target_node_label: str = "TailscaleGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("group_owners", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "OWNS"
    properties: TailscaleTagToGroupRelProperties = TailscaleTagToGroupRelProperties()


@dataclass(frozen=True)
class TailscaleTagToDeviceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:TailscaleDevice)-[:TAGGED]->(:TailscaleTag)
class TailscaleTagToDeviceRel(CartographyRelSchema):
    target_node_label: str = "TailscaleDevice"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("devices", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "TAGGED"
    properties: TailscaleTagToDeviceRelProperties = TailscaleTagToDeviceRelProperties()


@dataclass(frozen=True)
class TailscaleTagSchema(CartographyNodeSchema):
    label: str = "TailscaleTag"
    properties: TailscaleTagNodeProperties = TailscaleTagNodeProperties()
    sub_resource_relationship: TailscaleTagToTailnetRel = TailscaleTagToTailnetRel()
    other_relationships = OtherRelationships(
        [
            TailscaleTagToGroupRel(),
            TailscaleTagToUserRel(),
            TailscaleTagToDeviceRel(),
        ]
    )
