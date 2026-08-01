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
class RailwayVolumeInstanceNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="ID of the Railway volume instance."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    volume_id: PropertyRef = PropertyRef(
        "volumeId", extra_index=True, description="ID of the parent volume."
    )
    # Denormalised from the parent volume: the instance itself has no name, and the
    # BlockStorage ontology needs one that is not a mount path.
    volume_name: PropertyRef = PropertyRef(
        "volume_name", extra_index=True, description="Name of the parent volume."
    )
    environment_id: PropertyRef = PropertyRef(
        "environmentId",
        extra_index=True,
        description="ID of the environment containing the disk.",
    )
    service_id: PropertyRef = PropertyRef(
        "serviceId",
        extra_index=True,
        description="ID of the service that mounts the disk.",
    )
    mount_path: PropertyRef = PropertyRef(
        "mountPath", description="Path where the disk is mounted in the service."
    )
    region: PropertyRef = PropertyRef(
        "region", extra_index=True, description="Region where the disk is provisioned."
    )
    size_mb: PropertyRef = PropertyRef(
        "sizeMB", description="Provisioned size in megabytes."
    )
    # Derived in transform() from size_mb, for the BlockStorage ontology mapping.
    size_gb: PropertyRef = PropertyRef(
        "size_gb", description="Provisioned size in gigabytes."
    )
    current_size_mb: PropertyRef = PropertyRef(
        "currentSizeMB", description="Currently used space in megabytes."
    )
    state: PropertyRef = PropertyRef(
        "state", extra_index=True, description="Lifecycle state of the disk."
    )
    created_at: PropertyRef = PropertyRef(
        "createdAt", description="Time when the disk was created."
    )


@dataclass(frozen=True)
class RailwayVolumeInstanceToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:RailwayProject)-[:RESOURCE]->(:RailwayVolumeInstance)
class RailwayVolumeInstanceToProjectRel(CartographyRelSchema):
    """Connects a Railway project to a volume instance that it contains."""

    target_node_label: str = "RailwayProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: RailwayVolumeInstanceToProjectRelProperties = (
        RailwayVolumeInstanceToProjectRelProperties()
    )


@dataclass(frozen=True)
class RailwayVolumeInstanceToVolumeRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:RailwayVolume)-[:HAS]->(:RailwayVolumeInstance)
class RailwayVolumeInstanceToVolumeRel(CartographyRelSchema):
    """Connects a Railway volume definition to one of its environment-specific disks."""

    target_node_label: str = "RailwayVolume"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("volumeId")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS"
    properties: RailwayVolumeInstanceToVolumeRelProperties = (
        RailwayVolumeInstanceToVolumeRelProperties()
    )


@dataclass(frozen=True)
class RailwayVolumeInstanceToServiceInstanceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:RailwayServiceInstance)-[:MOUNTS]->(:RailwayVolumeInstance)
# Matches the ScalewayInstance-[:MOUNTS]->ScalewayVolume vocabulary.
class RailwayVolumeInstanceToServiceInstanceRel(CartographyRelSchema):
    """Identifies the Railway service instance that mounts a disk."""

    target_node_label: str = "RailwayServiceInstance"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "service_id": PropertyRef("serviceId"),
            "environment_id": PropertyRef("environmentId"),
        },
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "MOUNTS"
    properties: RailwayVolumeInstanceToServiceInstanceRelProperties = (
        RailwayVolumeInstanceToServiceInstanceRelProperties()
    )


@dataclass(frozen=True)
class RailwayVolumeInstanceSchema(CartographyNodeSchema):
    """A persistent Railway disk provisioned for one environment."""

    label: str = "RailwayVolumeInstance"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([BLOCK_STORAGE])
    properties: RailwayVolumeInstanceNodeProperties = (
        RailwayVolumeInstanceNodeProperties()
    )
    sub_resource_relationship: RailwayVolumeInstanceToProjectRel = (
        RailwayVolumeInstanceToProjectRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            RailwayVolumeInstanceToVolumeRel(),
            RailwayVolumeInstanceToServiceInstanceRel(),
        ],
    )
