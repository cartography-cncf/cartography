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
class TencentCloudCBSDiskNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Disk ID, e.g. `disk-11112222`.")
    name: PropertyRef = PropertyRef("name", description="Name of the disk.")
    region: PropertyRef = PropertyRef(
        "region", extra_index=True, description="Region the disk is in."
    )
    zone: PropertyRef = PropertyRef(
        "zone", description="Availability zone of the disk."
    )
    project_id: PropertyRef = PropertyRef(
        "project_id", description="ID of the Tencent Cloud project the disk belongs to."
    )
    disk_type: PropertyRef = PropertyRef(
        "disk_type", description="Disk medium, e.g. `CLOUD_PREMIUM`, `CLOUD_SSD`."
    )
    disk_usage: PropertyRef = PropertyRef(
        "disk_usage", description="`SYSTEM_DISK` or `DATA_DISK`."
    )
    disk_size: PropertyRef = PropertyRef("disk_size", description="Size, in GiB.")
    disk_state: PropertyRef = PropertyRef(
        "disk_state", description="Disk state, e.g. `ATTACHED`, `UNATTACHED`."
    )
    attached: PropertyRef = PropertyRef(
        "attached", description="`True` when the disk is attached to an instance."
    )
    encrypt: PropertyRef = PropertyRef(
        "encrypt", description="`True` when the disk is encrypted."
    )
    kms_key_id: PropertyRef = PropertyRef(
        "kms_key_id", description="ID of the KMS key that encrypts the disk."
    )
    shareable: PropertyRef = PropertyRef(
        "shareable", description="`True` for a disk that several instances can attach."
    )
    portable: PropertyRef = PropertyRef(
        "portable", description="`True` for an elastic disk that can be detached."
    )
    delete_with_instance: PropertyRef = PropertyRef(
        "delete_with_instance",
        description="`True` when the disk is destroyed with its instance.",
    )
    snapshot_count: PropertyRef = PropertyRef(
        "snapshot_count", description="Number of snapshots of the disk."
    )
    disk_charge_type: PropertyRef = PropertyRef(
        "disk_charge_type",
        description="Billing mode, e.g. `PREPAID`, `POSTPAID_BY_HOUR`.",
    )
    tags: PropertyRef = PropertyRef(
        "tags", description="Tags on the disk, as `key:value` strings."
    )
    create_time: PropertyRef = PropertyRef(
        "create_time", description="Time the disk was created."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class TencentCloudCBSDiskToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:TencentCloudAccount)-[:RESOURCE]->(:TencentCloudCBSDisk)
class TencentCloudCBSDiskToAccountRel(CartographyRelSchema):
    """Connects a `TencentCloudAccount` to its cloud disks."""

    target_node_label: str = "TencentCloudAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: TencentCloudCBSDiskToAccountRelProperties = (
        TencentCloudCBSDiskToAccountRelProperties()
    )


@dataclass(frozen=True)
class TencentCloudCBSDiskToCVMInstanceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:TencentCloudCBSDisk)-[:ATTACHED_TO]->(:TencentCloudCVMInstance)
class TencentCloudCBSDiskToCVMInstanceRel(CartographyRelSchema):
    """Connects a disk to each instance it is attached to."""

    target_node_label: str = "TencentCloudCVMInstance"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("attached_instance_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ATTACHED_TO"
    properties: TencentCloudCBSDiskToCVMInstanceRelProperties = (
        TencentCloudCBSDiskToCVMInstanceRelProperties()
    )


@dataclass(frozen=True)
class TencentCloudCBSDiskSchema(CartographyNodeSchema):
    """A Cloud Block Storage (CBS) disk."""

    label: str = "TencentCloudCBSDisk"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([BLOCK_STORAGE])
    properties: TencentCloudCBSDiskNodeProperties = TencentCloudCBSDiskNodeProperties()
    sub_resource_relationship: TencentCloudCBSDiskToAccountRel = (
        TencentCloudCBSDiskToAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [TencentCloudCBSDiskToCVMInstanceRel()],
    )
