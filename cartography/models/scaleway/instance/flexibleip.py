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
class ScalewayFlexibleIpProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    address: PropertyRef = PropertyRef("address")
    reverse: PropertyRef = PropertyRef("reverse")
    tags: PropertyRef = PropertyRef("tags")
    type: PropertyRef = PropertyRef("type")
    state: PropertyRef = PropertyRef("state")
    prefix: PropertyRef = PropertyRef("prefix")
    ipam_id: PropertyRef = PropertyRef("ipam_id")
    zone: PropertyRef = PropertyRef("zone")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ScalewayFlexibleIpToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayProject)-[:RESOURCE]->(:ScalewayFlexibleIp)
class ScalewayFlexibleIpToProjectRel(CartographyRelSchema):
    target_node_label: str = "ScalewayProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ScalewayFlexibleIpToProjectRelProperties = (
        ScalewayFlexibleIpToProjectRelProperties()
    )


@dataclass(frozen=True)
class ScalewayFlexibleIpSchema(CartographyNodeSchema):
    label: str = "ScalewayFlexibleIp"
    properties: ScalewayFlexibleIpProperties = ScalewayFlexibleIpProperties()
    sub_resource_relationship: ScalewayFlexibleIpToProjectRel = (
        ScalewayFlexibleIpToProjectRel()
    )
