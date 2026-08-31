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
class UnikraftVolumeNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "uuid",
        description=(
            "Unikraft volume UUID. Assumed globally unique across metros; "
            "see UnikraftInstanceNodeProperties.id."
        ),
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Volume name."
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="Creation timestamp."
    )
    state: PropertyRef = PropertyRef("state", description="Volume lifecycle state.")
    size_mb: PropertyRef = PropertyRef("size_mb", description="Volume size in MB.")
    size_gb: PropertyRef = PropertyRef(
        "size_gb",
        description="Volume size in GB, rounded from size_mb for cross-provider queries.",
    )
    persistent: PropertyRef = PropertyRef(
        "persistent", description="Whether the volume persists across restarts."
    )
    tags: PropertyRef = PropertyRef(
        "tags", description="Tags associated with the volume."
    )
    status: PropertyRef = PropertyRef(
        "status", description="Operation status of the volume."
    )
    message: PropertyRef = PropertyRef(
        "message", description="Additional status information."
    )
    quota_policy: PropertyRef = PropertyRef(
        "quota_policy", description="Quota policy applied to the volume."
    )
    filesystem: PropertyRef = PropertyRef("filesystem", description="Filesystem type.")
    access_mode: PropertyRef = PropertyRef(
        "access_mode", description="Volume access mode."
    )
    metro: PropertyRef = PropertyRef(
        "METRO",
        set_in_kwargs=True,
        description="Unikraft metro this volume is provisioned in.",
    )
    account_id: PropertyRef = PropertyRef(
        "ACCOUNT_ID", set_in_kwargs=True, description="Unikraft account UUID."
    )


@dataclass(frozen=True)
class UnikraftVolumeToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:UnikraftAccount)-[:RESOURCE]->(:UnikraftVolume)
class UnikraftVolumeToAccountRel(CartographyRelSchema):
    """Connects `UnikraftAccount` to `UnikraftVolume` through `RESOURCE`."""

    target_node_label: str = "UnikraftAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: UnikraftVolumeToAccountRelProperties = (
        UnikraftVolumeToAccountRelProperties()
    )


@dataclass(frozen=True)
class UnikraftInstanceToVolumeMountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:UnikraftInstance)-[:MOUNTS]->(:UnikraftVolume)
class UnikraftInstanceToVolumeMountRel(CartographyRelSchema):
    """Connects `UnikraftInstance` to a mounted `UnikraftVolume`."""

    target_node_label: str = "UnikraftInstance"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("mounted_by_instance_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "MOUNTS"
    properties: UnikraftInstanceToVolumeMountRelProperties = (
        UnikraftInstanceToVolumeMountRelProperties()
    )


@dataclass(frozen=True)
class UnikraftVolumeSchema(CartographyNodeSchema):
    """Represents a Unikraft Cloud persistent volume."""

    label: str = "UnikraftVolume"
    properties: UnikraftVolumeNodeProperties = UnikraftVolumeNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([BLOCK_STORAGE])
    sub_resource_relationship: UnikraftVolumeToAccountRel = UnikraftVolumeToAccountRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [UnikraftInstanceToVolumeMountRel()],
    )
