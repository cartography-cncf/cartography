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
from cartography.models.ontology.labels import FILE_STORAGE


@dataclass(frozen=True)
class ModalVolumeNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Volume ID, e.g. `vo-Fq2DSfh5sU2E9kQ6R9oDrj`."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Volume name."
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="When the volume was created."
    )
    # Workspace username of the creator, not an email.
    created_by: PropertyRef = PropertyRef(
        "created_by", extra_index=True, description="Workspace username of the creator."
    )
    # Raw VOLUME_FS_VERSION_* value. V1 volumes are the older filesystem generation.
    version: PropertyRef = PropertyRef(
        "version",
        extra_index=True,
        description="Raw `VOLUME_FS_VERSION_*` value. V1 is the older filesystem generation.",
    )
    environment_name: PropertyRef = PropertyRef(
        "environment_name",
        extra_index=True,
        description="Name of the owning environment.",
    )


@dataclass(frozen=True)
class ModalVolumeToEnvironmentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ModalEnvironment)-[:RESOURCE]->(:ModalVolume)
class ModalVolumeToEnvironmentRel(CartographyRelSchema):
    target_node_label: str = "ModalEnvironment"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ENVIRONMENT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ModalVolumeToEnvironmentRelProperties = (
        ModalVolumeToEnvironmentRelProperties()
    )


@dataclass(frozen=True)
class ModalVolumeToCreatorRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ModalVolume)-[:CREATED_BY]->(:ModalUser)
# Modal reports the creator as a workspace username, resolved to a ModalUser id by the
# intel layer against this workspace's members. Absent when the creator is no longer a member.
class ModalVolumeToCreatorRel(CartographyRelSchema):
    target_node_label: str = "ModalUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("created_by_user_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "CREATED_BY"
    properties: ModalVolumeToCreatorRelProperties = ModalVolumeToCreatorRelProperties()


@dataclass(frozen=True)
# A Modal volume: a persistent, shared filesystem mountable by workloads.
#
# FileStorage rather than BlockStorage: a Modal volume is a distributed filesystem mounted at
# a path by many containers at once, not a block device attached to one instance.
#
# Which workloads mount it is NOT graphable: `Function.volume_mounts` is write-only in Modal's
# API, the same limitation as secrets.
class ModalVolumeSchema(CartographyNodeSchema):
    """Represents a Modal volume: a persistent distributed filesystem that many containers can mount at once. Which workloads mount it is **not** graphable: `Function.volume_mounts` is write-only, the same limitation as secrets."""

    label: str = "ModalVolume"
    properties: ModalVolumeNodeProperties = ModalVolumeNodeProperties()
    sub_resource_relationship: ModalVolumeToEnvironmentRel = (
        ModalVolumeToEnvironmentRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [ModalVolumeToCreatorRel()],
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([FILE_STORAGE])
