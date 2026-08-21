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
class RenderDiskNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="ID of the Render disk.")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Name of the disk."
    )
    owner_id: PropertyRef = PropertyRef(
        "ownerId", description="ID of the owning Render workspace."
    )
    service_id: PropertyRef = PropertyRef(
        "serviceId",
        extra_index=True,
        description="ID of the service the disk is attached to.",
    )
    size_gb: PropertyRef = PropertyRef("sizeGB", description="Size of the disk in GB.")
    mount_path: PropertyRef = PropertyRef(
        "mountPath", description="Filesystem path the disk is mounted at."
    )
    created_at: PropertyRef = PropertyRef(
        "createdAt", description="Time when the disk was created."
    )
    updated_at: PropertyRef = PropertyRef(
        "updatedAt", description="Time when the disk was last modified."
    )


@dataclass(frozen=True)
class RenderDiskToTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:RenderTenant)-[:RESOURCE]->(:RenderDisk)
class RenderDiskToTenantRel(CartographyRelSchema):
    """Connects a Render workspace to a disk that it contains."""

    target_node_label: str = "RenderTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("OWNER_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: RenderDiskToTenantRelProperties = RenderDiskToTenantRelProperties()


@dataclass(frozen=True)
class RenderDiskToServiceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:RenderService)-[:MOUNTS]->(:RenderDisk)
class RenderDiskToServiceRel(CartographyRelSchema):
    """Connects a Render service to the disk mounted on it."""

    target_node_label: str = "RenderService"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("serviceId")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "MOUNTS"
    properties: RenderDiskToServiceRelProperties = RenderDiskToServiceRelProperties()


@dataclass(frozen=True)
class RenderDiskSchema(CartographyNodeSchema):
    """A Render persistent disk attached to a service."""

    label: str = "RenderDisk"
    properties: RenderDiskNodeProperties = RenderDiskNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([BLOCK_STORAGE])
    sub_resource_relationship: RenderDiskToTenantRel = RenderDiskToTenantRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [RenderDiskToServiceRel()],
    )
