from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class EfsFileSystemNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("FileSystemId")
    arn: PropertyRef = PropertyRef("FileSystemArn", extra_index=True)
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    owner_id: PropertyRef = PropertyRef("OwnerId")
    creation_token: PropertyRef = PropertyRef("CreationToken")
    creation_time: PropertyRef = PropertyRef("CreationTime")
    lifecycle_state: PropertyRef = PropertyRef("LifeCycleState")
    name: PropertyRef = PropertyRef("Name")
    number_of_mount_targets: PropertyRef = PropertyRef("NumberOfMountTargets")
    size_in_bytes_value: PropertyRef = PropertyRef("SizeInBytesValue")
    size_in_bytes_timestamp: PropertyRef = PropertyRef("SizeInBytesTimestamp")
    performance_mode: PropertyRef = PropertyRef("PerformanceMode")
    encrypted: PropertyRef = PropertyRef("Encrypted")
    kms_key_id: PropertyRef = PropertyRef("KmsKeyId")
    throughput_mode: PropertyRef = PropertyRef("ThroughputMode")
    availability_zone_name: PropertyRef = PropertyRef("AvailabilityZoneName")
    availability_zone_id: PropertyRef = PropertyRef("AvailabilityZoneId")
    file_system_protection: PropertyRef = PropertyRef("FileSystemProtection")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EfsFileSystemToAwsAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EfsFileSystemToAWSAccountRel(CartographyRelSchema):
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
class EfsFileSystemSchema(CartographyNodeSchema):
    label: str = "EfsFileSystem"
    properties: EfsFileSystemNodeProperties = EfsFileSystemNodeProperties()
    sub_resource_relationship: EfsFileSystemToAWSAccountRel = (
        EfsFileSystemToAWSAccountRel()
    )
