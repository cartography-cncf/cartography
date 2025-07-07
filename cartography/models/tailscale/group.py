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
class TailscaleGroupNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name")


@dataclass(frozen=True)
class TailscaleGroupToTailnetRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:TailscaleTailnet)-[:RESOURCE]->(:TailscaleGroup)
class TailscaleGroupToTailnetRel(CartographyRelSchema):
    target_node_label: str = "TailscaleTailnet"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("org", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: TailscaleGroupToTailnetRelProperties = (
        TailscaleGroupToTailnetRelProperties()
    )


@dataclass(frozen=True)
class TailscaleGroupToUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:TailscaleUser)-[:MEMBER_OF]->(:TailscaleGroup)
class TailscaleGroupToUserRel(CartographyRelSchema):
    target_node_label: str = "TailscaleUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"login_name": PropertyRef("members", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "MEMBER_OF"
    properties: TailscaleGroupToUserRelProperties = TailscaleGroupToUserRelProperties()


@dataclass(frozen=True)
class TailscaleGroupToGroupRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:TailscaleGroup)-[:MEMBER_OF]->(:TailscaleGroup)
class TailscaleGroupToGroupRel(CartographyRelSchema):
    target_node_label: str = "TailscaleGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("sub_groups", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "MEMBER_OF"
    properties: TailscaleGroupToGroupRelProperties = (
        TailscaleGroupToGroupRelProperties()
    )


@dataclass(frozen=True)
class TailscaleGroupSchema(CartographyNodeSchema):
    label: str = "TailscaleGroup"
    properties: TailscaleGroupNodeProperties = TailscaleGroupNodeProperties()
    sub_resource_relationship: TailscaleGroupToTailnetRel = TailscaleGroupToTailnetRel()
    other_relationships = OtherRelationships(
        [
            TailscaleGroupToGroupRel(),
            TailscaleGroupToUserRel(),
        ]
    )
