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
class ScalewayVolumeSnapshotNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name")
    tags: PropertyRef = PropertyRef("tags")
    volume_type: PropertyRef = PropertyRef("volume_type")
    size: PropertyRef = PropertyRef("size")
    state: PropertyRef = PropertyRef("state")
    creation_date: PropertyRef = PropertyRef("creation_date")
    modification_date: PropertyRef = PropertyRef("modification_date")
    error_reason: PropertyRef = PropertyRef("error_reason")
    zone: PropertyRef = PropertyRef("zone")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ScalewayVolumeSnapshotToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayProject)-[:RESOURCE]->(:ScalewayVolumeSnapshot)
class ScalewayVolumeSnapshotToProjectRel(CartographyRelSchema):
    target_node_label: str = "ScalewayProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ScalewayVolumeSnapshotToProjectRelProperties = (
        ScalewayVolumeSnapshotToProjectRelProperties()
    )


@dataclass(frozen=True)
class ScalewayVolumeSnapshotToInstanceVolumeProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayVolume)-[:HAS]->(:ScalewayVolumeSnapshot)
class ScalewayVolumeSnapshotToInstanceVolumeRel(CartographyRelSchema):
    target_node_label: str = "ScalewayVolume"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("base_volume.id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS"
    properties: ScalewayVolumeSnapshotToInstanceVolumeProperties = (
        ScalewayVolumeSnapshotToInstanceVolumeProperties()
    )


@dataclass(frozen=True)
class ScalewayVolumeSnapshotSchema(CartographyNodeSchema):
    label: str = "ScalewayVolumeSnapshot"
    properties: ScalewayVolumeSnapshotNodeProperties = (
        ScalewayVolumeSnapshotNodeProperties()
    )
    sub_resource_relationship: ScalewayVolumeSnapshotToProjectRel = (
        ScalewayVolumeSnapshotToProjectRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        rels=[ScalewayVolumeSnapshotToInstanceVolumeRel()],
    )
