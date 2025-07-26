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
class ScalewayVolumeNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name")
    export_uri: PropertyRef = PropertyRef("export_uri")
    size: PropertyRef = PropertyRef("size")
    volume_type: PropertyRef = PropertyRef("volume_type")
    creation_date: PropertyRef = PropertyRef("creation_date")
    modification_date: PropertyRef = PropertyRef("modification_date")
    tags: PropertyRef = PropertyRef("tags")
    state: PropertyRef = PropertyRef("state")
    zone: PropertyRef = PropertyRef("zone")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ScalewayVolumeToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayProject)-[:RESOURCE]->(:ScalewayVolume)
class ScalewayVolumeToProjectRel(CartographyRelSchema):
    target_node_label: str = "ScalewayProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ScalewayVolumeToProjectRelProperties = (
        ScalewayVolumeToProjectRelProperties()
    )


@dataclass(frozen=True)
class ScalewayVolumeSchema(CartographyNodeSchema):
    label: str = "ScalewayVolume"
    properties: ScalewayVolumeNodeProperties = ScalewayVolumeNodeProperties()
    sub_resource_relationship: ScalewayVolumeToProjectRel = ScalewayVolumeToProjectRel()
