from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class ScalewayVolumeSnapshotNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Snapshot ID.")
    name: PropertyRef = PropertyRef("name", description="Snapshot name.")
    tags: PropertyRef = PropertyRef("tags", description="Snapshot tags.")
    volume_type: PropertyRef = PropertyRef(
        "volume_type",
        description="Snapshot volume type (`l_ssd`, `b_ssd`, `unified`, `scratch`, `sbs_volume`, `sbs_snapshot`)",
    )
    size: PropertyRef = PropertyRef("size", description="Snapshot size. (in bytes)")
    state: PropertyRef = PropertyRef(
        "state",
        description="Snapshot state (`available`, `snapshotting`, `error`, `invalid_data`, `importing`, `exporting`)",
    )
    creation_date: PropertyRef = PropertyRef(
        "creation_date", description="Snapshot creation date."
    )
    modification_date: PropertyRef = PropertyRef(
        "modification_date", description="Snapshot modification date."
    )
    error_reason: PropertyRef = PropertyRef(
        "error_reason", description="Reason for the failed snapshot import."
    )
    zone: PropertyRef = PropertyRef("zone", description="Snapshot zone.")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated", set_in_kwargs=True, description="Timestamp of the last update"
    )


@dataclass(frozen=True)
class ScalewayVolumeSnapshotToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayProject)-[:RESOURCE]->(:ScalewayVolumeSnapshot)
class ScalewayVolumeSnapshotToProjectRel(CartographyRelSchema):
    """Connects `ScalewayProject` to `ScalewayVolumeSnapshot` through `RESOURCE`."""

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
class ScalewayVolumeSnapshotToInstanceVolumeRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayVolume)-[:HAS]->(:ScalewayVolumeSnapshot)
class ScalewayVolumeSnapshotToInstanceVolumeRel(CartographyRelSchema):
    """Connects `ScalewayVolume` to `ScalewayVolumeSnapshot` through `HAS`."""

    target_node_label: str = "ScalewayVolume"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("base_volume.id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS"
    properties: ScalewayVolumeSnapshotToInstanceVolumeRelProperties = (
        ScalewayVolumeSnapshotToInstanceVolumeRelProperties()
    )


@dataclass(frozen=True)
class ScalewayVolumeSnapshotSchema(CartographyNodeSchema):
    """A snapshot takes a picture of a volume at one specific point in time. For a complete
    backup of your Instance, you can create an image.
    """

    label: str = "ScalewayVolumeSnapshot"
    properties: ScalewayVolumeSnapshotNodeProperties = (
        ScalewayVolumeSnapshotNodeProperties()
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Snapshot"])
    sub_resource_relationship: ScalewayVolumeSnapshotToProjectRel = (
        ScalewayVolumeSnapshotToProjectRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        rels=[ScalewayVolumeSnapshotToInstanceVolumeRel()],
    )
