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
class ScalewayVolumeNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Volume unique ID.")
    name: PropertyRef = PropertyRef("name", description="Volume name.")
    export_uri: PropertyRef = PropertyRef(
        "export_uri", description="Show the volume NBD export URI."
    )
    size: PropertyRef = PropertyRef("size", description="Volume disk size. (in bytes)")
    size_gb: PropertyRef = PropertyRef(
        "size_gb",
        description="Volume disk size derived in gigabytes (rounded from `size`).",
    )
    volume_type: PropertyRef = PropertyRef(
        "volume_type",
        description="Volume type (`l_ssd`, `b_ssd`, `unified`, `scratch`, `sbs_volume`, `sbs_snapshot`)",
    )
    creation_date: PropertyRef = PropertyRef(
        "creation_date", description="Volume creation date."
    )
    modification_date: PropertyRef = PropertyRef(
        "modification_date", description="Volume modification date."
    )
    tags: PropertyRef = PropertyRef("tags", description="Volume tags.")
    state: PropertyRef = PropertyRef(
        "state",
        description="Volume state (`available`, `snapshotting`, `fetching`, `resizing`, `saving`, `hotsyncing`, `error`)",
    )
    zone: PropertyRef = PropertyRef(
        "zone", description="Zone in which the volume is located."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated", set_in_kwargs=True, description="Timestamp of the last update"
    )


@dataclass(frozen=True)
class ScalewayVolumeToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayProject)-[:RESOURCE]->(:ScalewayVolume)
class ScalewayVolumeToProjectRel(CartographyRelSchema):
    """Connects `ScalewayProject` to `ScalewayVolume` through `RESOURCE`."""

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
    """Volumes are storage space used by your Instances. You can attach several volumes to
    an Instance.
    """

    label: str = "ScalewayVolume"
    properties: ScalewayVolumeNodeProperties = ScalewayVolumeNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["BlockStorage"])
    sub_resource_relationship: ScalewayVolumeToProjectRel = ScalewayVolumeToProjectRel()
