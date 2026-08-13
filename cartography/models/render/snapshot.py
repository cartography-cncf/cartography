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
class RenderSnapshotNodeProperties(CartographyNodeProperties):
    # Render's snapshot objects have no id of their own, only a `snapshotKey` that the
    # docs say expires after 24h and is reissued (a *new* key) on re-query - so it is
    # not a stable identity to MERGE on across syncs. `<disk id>/<createdAt>` is used
    # instead: createdAt reflects when the underlying snapshot was actually taken, and
    # is stable for the same snapshot across syncs even as its key rotates.
    id: PropertyRef = PropertyRef(
        "id", description="Synthetic id: `<disk id>/<createdAt>`."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    owner_id: PropertyRef = PropertyRef(
        "ownerId", description="ID of the owning Render workspace."
    )
    disk_id: PropertyRef = PropertyRef(
        "diskId", extra_index=True, description="ID of the disk this is a snapshot of."
    )
    instance_id: PropertyRef = PropertyRef(
        "instanceId",
        description="ID of the service instance the snapshotted disk was attached to.",
    )
    created_at: PropertyRef = PropertyRef(
        "createdAt", description="Time when the snapshot was taken."
    )


@dataclass(frozen=True)
class RenderSnapshotToTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:RenderTenant)-[:RESOURCE]->(:RenderSnapshot)
class RenderSnapshotToTenantRel(CartographyRelSchema):
    """Connects a Render workspace to a disk snapshot that it contains."""

    target_node_label: str = "RenderTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("OWNER_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: RenderSnapshotToTenantRelProperties = (
        RenderSnapshotToTenantRelProperties()
    )


@dataclass(frozen=True)
class RenderSnapshotToDiskRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:RenderDisk)-[:HAS_SNAPSHOT]->(:RenderSnapshot)
class RenderSnapshotToDiskRel(CartographyRelSchema):
    """Connects a Render disk to a point-in-time snapshot of it."""

    target_node_label: str = "RenderDisk"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("diskId")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_SNAPSHOT"
    properties: RenderSnapshotToDiskRelProperties = RenderSnapshotToDiskRelProperties()


@dataclass(frozen=True)
class RenderSnapshotSchema(CartographyNodeSchema):
    """A point-in-time snapshot of a Render persistent disk."""

    label: str = "RenderSnapshot"
    properties: RenderSnapshotNodeProperties = RenderSnapshotNodeProperties()
    sub_resource_relationship: RenderSnapshotToTenantRel = RenderSnapshotToTenantRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [RenderSnapshotToDiskRel()],
    )
