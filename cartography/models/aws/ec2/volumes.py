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
class EBSVolumeNodeProperties(CartographyNodeProperties):
    arn: PropertyRef = PropertyRef("Arn", extra_index=True)
    id: PropertyRef = PropertyRef("VolumeId")
    volumeid: PropertyRef = PropertyRef("VolumeId", extra_index=True)
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    availabilityzone: PropertyRef = PropertyRef("AvailabilityZone")
    createtime: PropertyRef = PropertyRef("CreateTime")
    encrypted: PropertyRef = PropertyRef("Encrypted")
    size: PropertyRef = PropertyRef("Size")
    state: PropertyRef = PropertyRef("State")
    outpostarn: PropertyRef = PropertyRef("OutpostArn")
    snapshotid: PropertyRef = PropertyRef("SnapshotId")
    iops: PropertyRef = PropertyRef("Iops")
    fastrestored: PropertyRef = PropertyRef("FastRestored")
    multiattachenabled: PropertyRef = PropertyRef("MultiAttachEnabled")
    type: PropertyRef = PropertyRef("VolumeType")
    kmskeyid: PropertyRef = PropertyRef("KmsKeyId")


@dataclass(frozen=True)
class EBSVolumeToAWSAccountRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EBSVolumeToAWSAccountRel(CartographyRelSchema):
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
    target_node_label: str = "EC2Instance"
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
    target_node_label: str = "EBSSnapshot"
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
    """
    EBS Volume properties as returned from the EBS Volume API response
    """

    label: str = "EBSVolume"
    properties: EBSVolumeNodeProperties = EBSVolumeNodeProperties()
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

    arn: PropertyRef = PropertyRef("Arn", extra_index=True)
    id: PropertyRef = PropertyRef("VolumeId")
    volumeid: PropertyRef = PropertyRef("VolumeId", extra_index=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    deleteontermination: PropertyRef = PropertyRef("DeleteOnTermination")


@dataclass(frozen=True)
class EBSVolumeInstanceSchema(CartographyNodeSchema):
    """
    EBS Volume from EC2 Instance API response. This is separate from `EBSVolumeSchema` to prevent issue #1210.
    """

    label: str = "EBSVolume"
    properties: EBSVolumeInstanceProperties = EBSVolumeInstanceProperties()
    sub_resource_relationship: EBSVolumeToAWSAccountRel = EBSVolumeToAWSAccountRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            EBSVolumeToEC2InstanceRel(),
            EBSVolumeToEBSSnapshotRel(),
        ],
    )
