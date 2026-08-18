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
from cartography.models.ontology.labels import BLOCK_STORAGE


@dataclass(frozen=True)
class FlyVolumeNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Fly Volume ID.")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Volume name."
    )
    type: PropertyRef = PropertyRef("type", description="Volume type.")
    state: PropertyRef = PropertyRef("state", description="Volume state.")
    size_gb: PropertyRef = PropertyRef("size_gb", description="Volume size in GB.")
    region: PropertyRef = PropertyRef("region", description="Fly.io region.")
    zone: PropertyRef = PropertyRef("zone", description="Fly.io zone.")
    encrypted: PropertyRef = PropertyRef(
        "encrypted", description="Whether the volume is encrypted."
    )
    attached_machine_id: PropertyRef = PropertyRef(
        "attached_machine_id", description="Attached Machine ID, if any."
    )
    attached_alloc_id: PropertyRef = PropertyRef(
        "attached_alloc_id", description="Attached allocation ID, if any."
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="Creation timestamp."
    )
    blocks: PropertyRef = PropertyRef("blocks", description="Total blocks.")
    block_size: PropertyRef = PropertyRef("block_size", description="Block size.")
    blocks_free: PropertyRef = PropertyRef("blocks_free", description="Free blocks.")
    blocks_avail: PropertyRef = PropertyRef(
        "blocks_avail", description="Available blocks."
    )
    bytes_used: PropertyRef = PropertyRef("bytes_used", description="Used bytes.")
    bytes_total: PropertyRef = PropertyRef("bytes_total", description="Total bytes.")
    fstype: PropertyRef = PropertyRef("fstype", description="Filesystem type.")
    snapshot_retention: PropertyRef = PropertyRef(
        "snapshot_retention", description="Snapshot retention in days."
    )
    auto_backup_enabled: PropertyRef = PropertyRef(
        "auto_backup_enabled", description="Whether automatic backups are enabled."
    )
    host_status: PropertyRef = PropertyRef("host_status", description="Host status.")
    host_dedication_key: PropertyRef = PropertyRef(
        "host_dedication_key", description="Host dedication key."
    )
    app_id: PropertyRef = PropertyRef("APP_ID", set_in_kwargs=True)


@dataclass(frozen=True)
class FlyVolumeToAppRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:FlyApp)-[:RESOURCE]->(:FlyVolume)
class FlyVolumeToAppRel(CartographyRelSchema):
    """Connects `FlyApp` to `FlyVolume` through `RESOURCE`."""

    target_node_label: str = "FlyApp"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("APP_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: FlyVolumeToAppRelProperties = FlyVolumeToAppRelProperties()


@dataclass(frozen=True)
class FlyMachineToVolumeMountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:FlyMachine)-[:MOUNTS]->(:FlyVolume)
class FlyMachineToVolumeMountRel(CartographyRelSchema):
    """Connects `FlyMachine` to a mounted Fly Volume."""

    target_node_label: str = "FlyMachine"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("attached_machine_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "MOUNTS"
    properties: FlyMachineToVolumeMountRelProperties = (
        FlyMachineToVolumeMountRelProperties()
    )


@dataclass(frozen=True)
class FlyVolumeSchema(CartographyNodeSchema):
    """Represents a Fly Volume."""

    label: str = "FlyVolume"
    properties: FlyVolumeNodeProperties = FlyVolumeNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([BLOCK_STORAGE])
    sub_resource_relationship: FlyVolumeToAppRel = FlyVolumeToAppRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            FlyMachineToVolumeMountRel(),
        ]
    )
