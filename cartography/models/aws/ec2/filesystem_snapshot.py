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
from cartography.models.ontology.labels import FILESYSTEM_SNAPSHOT


@dataclass(frozen=True)
class EC2FilesystemSnapshotNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Stable scan target ID in the form aws:ec2-rootfs:<instance-id>.",
    )
    instance_id: PropertyRef = PropertyRef(
        "instance_id",
        description="ID of the EC2 instance whose root filesystem is assessed.",
    )
    volume_id: PropertyRef = PropertyRef(
        "volume_id",
        description="ID of the EBS volume currently backing the instance's root filesystem.",
    )
    kind: PropertyRef = PropertyRef(
        "kind",
        extra_index=True,
        description="Filesystem snapshot type. Always `rootfs` for EC2 instances.",
    )
    region: PropertyRef = PropertyRef(
        "Region",
        set_in_kwargs=True,
        description="AWS region of the EC2 instance.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EC2FilesystemSnapshotToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EC2FilesystemSnapshotToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: EC2FilesystemSnapshotToAWSAccountRelProperties = (
        EC2FilesystemSnapshotToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class EC2FilesystemSnapshotToInstanceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EC2FilesystemSnapshotToInstanceRel(CartographyRelSchema):
    target_node_label: str = "AWSEC2Instance"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("instance_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "SCANNED_AS"
    properties: EC2FilesystemSnapshotToInstanceRelProperties = (
        EC2FilesystemSnapshotToInstanceRelProperties()
    )


@dataclass(frozen=True)
class EC2FilesystemSnapshotToVolumeRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EC2FilesystemSnapshotToVolumeRel(CartographyRelSchema):
    target_node_label: str = "AWSEBSVolume"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("volume_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "SNAPSHOT_OF"
    properties: EC2FilesystemSnapshotToVolumeRelProperties = (
        EC2FilesystemSnapshotToVolumeRelProperties()
    )


@dataclass(frozen=True)
class EC2FilesystemSnapshotSchema(CartographyNodeSchema):
    """A persistent root filesystem target, independent of temporary EBS snapshots."""

    label: str = "AWSEC2FilesystemSnapshot"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([FILESYSTEM_SNAPSHOT])
    properties: EC2FilesystemSnapshotNodeProperties = (
        EC2FilesystemSnapshotNodeProperties()
    )
    sub_resource_relationship: EC2FilesystemSnapshotToAWSAccountRel = (
        EC2FilesystemSnapshotToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [EC2FilesystemSnapshotToInstanceRel(), EC2FilesystemSnapshotToVolumeRel()],
    )
