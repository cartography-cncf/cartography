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
class EBSVolumeNodeProperties(CartographyNodeProperties):
    arn: PropertyRef = PropertyRef(
        "Arn",
        extra_index=True,
        description="The Amazon Resource Name (ARN) of the volume",
    )
    id: PropertyRef = PropertyRef(
        "VolumeId", description="The ID of the EBS Volume (same as volumeid)"
    )
    volumeid: PropertyRef = PropertyRef(
        "VolumeId", extra_index=True, description="The ID of the EBS Volume"
    )
    region: PropertyRef = PropertyRef(
        "Region", set_in_kwargs=True, description="The region of the volume."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )
    availabilityzone: PropertyRef = PropertyRef(
        "AvailabilityZone", description="The Availability Zone for the volume."
    )
    createtime: PropertyRef = PropertyRef(
        "CreateTime", description="The time stamp when volume creation was initiated."
    )
    encrypted: PropertyRef = PropertyRef(
        "Encrypted", description="Indicates whether the volume is encrypted."
    )
    size: PropertyRef = PropertyRef(
        "Size", description="The size of the volume, in GiBs."
    )
    state: PropertyRef = PropertyRef("State", description="The volume state.")
    outpostarn: PropertyRef = PropertyRef(
        "OutpostArn", description="The Amazon Resource Name (ARN) of the Outpost."
    )
    snapshotid: PropertyRef = PropertyRef("SnapshotId", description="The snapshot ID.")
    iops: PropertyRef = PropertyRef(
        "Iops", description="The number of I/O operations per second (IOPS)."
    )
    fastrestored: PropertyRef = PropertyRef(
        "FastRestored",
        description="Indicates whether the volume was created using fast snapshot restore.",
    )
    multiattachenabled: PropertyRef = PropertyRef(
        "MultiAttachEnabled",
        description="Indicates whether Amazon EBS Multi-Attach is enabled.",
    )
    type: PropertyRef = PropertyRef("VolumeType", description="The volume type.")
    kmskeyid: PropertyRef = PropertyRef(
        "KmsKeyId",
        description="The Amazon Resource Name (ARN) of the AWS Key Management Service (AWS KMS) customer master key (CMK) that was used to protect the volume encryption key for the volume.",
    )


@dataclass(frozen=True)
class EBSVolumeToAWSAccountRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EBSVolumeToAWSAccountRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSEBSVolume`."

    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: EBSVolumeToAWSAccountRelRelProperties = (
        EBSVolumeToAWSAccountRelRelProperties()
    )


@dataclass(frozen=True)
class EBSVolumeToEC2InstanceRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EBSVolumeToEC2InstanceRel(CartographyRelSchema):
    "Represents a `ATTACHED_TO` relationship from `AWSEBSVolume` to `AWSEC2Instance`."

    target_node_label: str = "AWSEC2Instance"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("InstanceId")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ATTACHED_TO"
    properties: EBSVolumeToEC2InstanceRelRelProperties = (
        EBSVolumeToEC2InstanceRelRelProperties()
    )


@dataclass(frozen=True)
class EBSVolumeToEBSSnapshotRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EBSVolumeToEBSSnapshotRel(CartographyRelSchema):
    "Represents a `CREATED_FROM` relationship from `AWSEBSSnapshot` to `AWSEBSVolume`."

    target_node_label: str = "AWSEBSSnapshot"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("SnapshotId")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CREATED_FROM"
    properties: EBSVolumeToEBSSnapshotRelProperties = (
        EBSVolumeToEBSSnapshotRelProperties()
    )


@dataclass(frozen=True)
class EBSVolumeSchema(CartographyNodeSchema):
    "Represents an Amazon Elastic Block Store (EBS) volume."

    # Implementation note:
    # EBS Volume properties as returned from the EBS Volume API response

    label: str = "AWSEBSVolume"
    properties: EBSVolumeNodeProperties = EBSVolumeNodeProperties()
    # DEPRECATED: legacy EBSVolume node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["EBSVolume", "BlockStorage"])
    sub_resource_relationship: EBSVolumeToAWSAccountRel = EBSVolumeToAWSAccountRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            EBSVolumeToEC2InstanceRel(),
            EBSVolumeToEBSSnapshotRel(),
        ],
    )


@dataclass(frozen=True)
class EBSVolumeInstanceProperties(CartographyNodeProperties):
    """
    EBS Volume properties as known by an EC2 instance.
    The EC2 instance API response includes a `deleteontermination` field and the volume id.
    """

    arn: PropertyRef = PropertyRef(
        "Arn",
        extra_index=True,
        description="The Amazon Resource Name (ARN) of the volume",
    )
    id: PropertyRef = PropertyRef(
        "VolumeId", description="The ID of the EBS Volume (same as volumeid)"
    )
    volumeid: PropertyRef = PropertyRef(
        "VolumeId", extra_index=True, description="The ID of the EBS Volume"
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )
    deleteontermination: PropertyRef = PropertyRef(
        "DeleteOnTermination",
        description="Indicates whether the volume is deleted on instance termination.",
    )


@dataclass(frozen=True)
class EBSVolumeInstanceSchema(CartographyNodeSchema):
    "Represents an Amazon Elastic Block Store (EBS) volume."

    # Implementation note:
    # EBS Volume from EC2 Instance API response. This is separate from `EBSVolumeSchema`
    # to prevent issue #1210.

    label: str = "AWSEBSVolume"
    properties: EBSVolumeInstanceProperties = EBSVolumeInstanceProperties()
    # DEPRECATED: legacy EBSVolume node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["EBSVolume", "BlockStorage"])
    sub_resource_relationship: EBSVolumeToAWSAccountRel = EBSVolumeToAWSAccountRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            EBSVolumeToEC2InstanceRel(),
            EBSVolumeToEBSSnapshotRel(),
        ],
    )
