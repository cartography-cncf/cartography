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
class EfsFileSystemNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "FileSystemId", description="The ID of the file system, assigned by Amazon EFS"
    )
    arn: PropertyRef = PropertyRef(
        "FileSystemArn",
        extra_index=True,
        description="Amazon Resource Name (ARN) for the EFS file system",
    )
    region: PropertyRef = PropertyRef(
        "Region", set_in_kwargs=True, description="The region of the file system"
    )
    owner_id: PropertyRef = PropertyRef(
        "OwnerId", description="The AWS account that created the file system"
    )
    creation_token: PropertyRef = PropertyRef(
        "CreationToken", description="The opaque string specified in the request"
    )
    creation_time: PropertyRef = PropertyRef(
        "CreationTime",
        description="The time that the file system was created, in seconds",
    )
    lifecycle_state: PropertyRef = PropertyRef(
        "LifeCycleState", description="The lifecycle phase of the file system"
    )
    name: PropertyRef = PropertyRef(
        "Name",
        description="If the file system has a name tag, Amazon EFS returns the value in this field",
    )
    number_of_mount_targets: PropertyRef = PropertyRef(
        "NumberOfMountTargets",
        description="The current number of mount targets that the file system has",
    )
    size_in_bytes_value: PropertyRef = PropertyRef(
        "SizeInBytesValue",
        description="Latest known metered size (in bytes) of data stored in the file system",
    )
    size_in_bytes_timestamp: PropertyRef = PropertyRef(
        "SizeInBytesTimestamp", description="Time at which that size was determined"
    )
    performance_mode: PropertyRef = PropertyRef(
        "PerformanceMode", description="The performance mode of the file system"
    )
    encrypted: PropertyRef = PropertyRef(
        "Encrypted",
        description="A Boolean value that, if true, indicates that the file system is encrypted",
    )
    kms_key_id: PropertyRef = PropertyRef(
        "KmsKeyId",
        description="The ID of an AWS KMS key used to protect the encrypted file system",
    )
    throughput_mode: PropertyRef = PropertyRef(
        "ThroughputMode", description="Displays the file system's throughput mode"
    )
    availability_zone_name: PropertyRef = PropertyRef(
        "AvailabilityZoneName",
        description="Describes the AWS Availability Zone in which the file system is located",
    )
    availability_zone_id: PropertyRef = PropertyRef(
        "AvailabilityZoneId",
        description="The unique and consistent identifier of the Availability Zone in which the file system is located",
    )
    file_system_protection: PropertyRef = PropertyRef(
        "FileSystemProtection",
        description="Describes the protection on the file system",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )


@dataclass(frozen=True)
class EfsFileSystemToAwsAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EfsFileSystemToAWSAccountRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSEfsFileSystem`."

    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: EfsFileSystemToAwsAccountRelProperties = (
        EfsFileSystemToAwsAccountRelProperties()
    )


@dataclass(frozen=True)
class EfsFileSystemToKMSKeyRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# Canonical ontology edge: (:FileStorage)-[:ENCRYPTED_BY]->(:EncryptionKey).
# Only created when the file system has a customer-managed KMS key (KmsKeyId is
# the key ARN).
class EfsFileSystemToKMSKeyRel(CartographyRelSchema):
    "Represents a `ENCRYPTED_BY` relationship from `AWSEfsFileSystem` to `AWSKMSKey`."

    target_node_label: str = "AWSKMSKey"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("KmsKeyId")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ENCRYPTED_BY"
    properties: EfsFileSystemToKMSKeyRelProperties = (
        EfsFileSystemToKMSKeyRelProperties()
    )


@dataclass(frozen=True)
class EfsFileSystemSchema(CartographyNodeSchema):
    "Represents an `AWSEfsFileSystem` node in the AWS graph."

    label: str = "AWSEfsFileSystem"
    properties: EfsFileSystemNodeProperties = EfsFileSystemNodeProperties()
    # DEPRECATED: legacy EfsFileSystem node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        ["EfsFileSystem", "FileStorage"]
    )
    sub_resource_relationship: EfsFileSystemToAWSAccountRel = (
        EfsFileSystemToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            EfsFileSystemToKMSKeyRel(),
        ]
    )
