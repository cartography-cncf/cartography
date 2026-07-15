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
class EBSSnapshotNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "SnapshotId", description="The ID of the EBS Snapshot."
    )
    snapshotid: PropertyRef = PropertyRef(
        "SnapshotId", extra_index=True, description="The snapshot ID."
    )
    description: PropertyRef = PropertyRef(
        "Description", description="The description of the snapshot."
    )
    ownerid: PropertyRef = PropertyRef(
        "OwnerId",
        description="Identifier of the owner linked to this `AWSEBSSnapshot` node.",
    )
    ispublic: PropertyRef = PropertyRef(
        "Public",
        description="Whether this `AWSEBSSnapshot` node is publicly accessible.",
    )
    encrypted: PropertyRef = PropertyRef(
        "Encrypted", description="Indicates whether the snapshot is encrypted."
    )
    progress: PropertyRef = PropertyRef(
        "Progress", description="The progress of the snapshot, as a percentage."
    )
    starttime: PropertyRef = PropertyRef(
        "StartTime", description="The time stamp when the snapshot was initiated."
    )
    state: PropertyRef = PropertyRef("State", description="The snapshot state.")
    statemessage: PropertyRef = PropertyRef(
        "StateMessage",
        description="Encrypted Amazon EBS snapshots are copied asynchronously. If a snapshot copy operation fails (for example, if the proper AWS Key Management Service (AWS KMS) permissions are not obtained) this field displays error state details to help you diagnose why the error occurred. This parameter is only returned by DescribeSnapshots .",
    )
    volumeid: PropertyRef = PropertyRef("VolumeId", description="The volume ID.")
    volumesize: PropertyRef = PropertyRef(
        "VolumeSize", description="The size of the volume, in GiB."
    )
    outpostarn: PropertyRef = PropertyRef(
        "OutpostArn",
        description="The ARN of the AWS Outpost on which the snapshot is stored.",
    )
    dataencryptionkeyid: PropertyRef = PropertyRef(
        "DataEncryptionKeyId",
        description="The data encryption key identifier for the snapshot.",
    )
    kmskeyid: PropertyRef = PropertyRef(
        "KmsKeyId",
        description="The Amazon Resource Name (ARN) of the AWS Key Management Service (AWS KMS) customer master key (CMK) that was used to protect the volume encryption key for the parent volume.",
    )
    region: PropertyRef = PropertyRef(
        "Region", set_in_kwargs=True, description="The region of the snapshot."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )


@dataclass(frozen=True)
class EBSSnapshotToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EBSSnapshotToAWSAccountRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSEBSSnapshot`."

    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("AWS_ID", set_in_kwargs=True),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: EBSSnapshotToAWSAccountRelProperties = (
        EBSSnapshotToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class EBSSnapshotSchema(CartographyNodeSchema):
    "Represents an `AWSEBSSnapshot` node in the AWS graph."

    label: str = "AWSEBSSnapshot"
    properties: EBSSnapshotNodeProperties = EBSSnapshotNodeProperties()
    # DEPRECATED: legacy EBSSnapshot node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["EBSSnapshot", "Snapshot"])
    sub_resource_relationship: EBSSnapshotToAWSAccountRel = EBSSnapshotToAWSAccountRel()
    other_relationships: OtherRelationships = OtherRelationships([])
