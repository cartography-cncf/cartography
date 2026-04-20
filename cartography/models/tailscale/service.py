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
class TailscaleServiceNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name")
    comment: PropertyRef = PropertyRef("comment")
    ipv4_address: PropertyRef = PropertyRef("ipv4_address")
    ipv6_address: PropertyRef = PropertyRef("ipv6_address")
    ports: PropertyRef = PropertyRef("ports")
    tags: PropertyRef = PropertyRef("tags")


@dataclass(frozen=True)
class TailscaleServiceToTailnetRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:TailscaleTailnet)-[:RESOURCE]->(:TailscaleService)
class TailscaleServiceToTailnetRel(CartographyRelSchema):
    target_node_label: str = "TailscaleTailnet"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("org", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: TailscaleServiceToTailnetRelProperties = (
        TailscaleServiceToTailnetRelProperties()
    )


@dataclass(frozen=True)
class TailscaleServiceToTagRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:TailscaleService)-[:TAGGED]->(:TailscaleTag)
class TailscaleServiceToTagRel(CartographyRelSchema):
    target_node_label: str = "TailscaleTag"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("tag_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "TAGGED"
    properties: TailscaleServiceToTagRelProperties = (
        TailscaleServiceToTagRelProperties()
    )


@dataclass(frozen=True)
class TailscaleServiceSchema(CartographyNodeSchema):
    label: str = "TailscaleService"
    properties: TailscaleServiceNodeProperties = TailscaleServiceNodeProperties()
    sub_resource_relationship: TailscaleServiceToTailnetRel = (
        TailscaleServiceToTailnetRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            TailscaleServiceToTagRel(),
        ],
    )
