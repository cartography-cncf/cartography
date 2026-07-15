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
class EfsMountTargetNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "MountTargetId", description="System-assigned mount target ID"
    )
    arn: PropertyRef = PropertyRef(
        "MountTargetId", extra_index=True, description="System-assigned mount target ID"
    )
    region: PropertyRef = PropertyRef(
        "Region", set_in_kwargs=True, description="The region of the mount target"
    )
    fileSystem_id: PropertyRef = PropertyRef(
        "FileSystemId",
        description="The ID of the file system for which the mount target is intended",
    )
    lifecycle_state: PropertyRef = PropertyRef(
        "LifeCycleState", description="Lifecycle state of the mount target"
    )
    mount_target_id: PropertyRef = PropertyRef(
        "MountTargetId", description="System-assigned mount target ID"
    )
    subnet_id: PropertyRef = PropertyRef(
        "SubnetId", description="The ID of the mount target's subnet"
    )
    availability_zone_id: PropertyRef = PropertyRef(
        "AvailabilityZoneId",
        description="The unique and consistent identifier of the Availability Zone that the mount target resides in",
    )
    availability_zone_name: PropertyRef = PropertyRef(
        "AvailabilityZoneName",
        description="The name of the Availability Zone in which the mount target is located",
    )
    ip_address: PropertyRef = PropertyRef(
        "IpAddress",
        description="Address at which the file system can be mounted by using the mount target",
    )
    network_interface_id: PropertyRef = PropertyRef(
        "NetworkInterfaceId",
        description="The ID of the network interface that Amazon EFS created when it created the mount target",
    )
    owner_id: PropertyRef = PropertyRef(
        "OwnerId", description="AWS account ID that owns the resource"
    )
    vpc_id: PropertyRef = PropertyRef(
        "VpcId",
        description="The virtual private cloud (VPC) ID that the mount target is configured in",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )


@dataclass(frozen=True)
class EfsMountTargetToAwsAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EfsMountTargetToAWSAccountRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSEfsMountTarget`."

    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: EfsMountTargetToAwsAccountRelProperties = (
        EfsMountTargetToAwsAccountRelProperties()
    )


@dataclass(frozen=True)
class EfsMountTargetToEfsFileSystemRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EfsMountTargetToEfsFileSystemRel(CartographyRelSchema):
    "Represents a `ATTACHED_TO` relationship from `AWSEfsMountTarget` to `AWSEfsFileSystem`."

    target_node_label: str = "AWSEfsFileSystem"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("FileSystemId")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ATTACHED_TO"
    properties: EfsMountTargetToEfsFileSystemRelProperties = (
        EfsMountTargetToEfsFileSystemRelProperties()
    )


@dataclass(frozen=True)
class EfsMountTargetSchema(CartographyNodeSchema):
    "Represents an `AWSEfsMountTarget` node in the AWS graph."

    label: str = "AWSEfsMountTarget"
    # DEPRECATED: legacy EfsMountTarget node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["EfsMountTarget"])
    properties: EfsMountTargetNodeProperties = EfsMountTargetNodeProperties()
    sub_resource_relationship: EfsMountTargetToAWSAccountRel = (
        EfsMountTargetToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            EfsMountTargetToEfsFileSystemRel(),
        ]
    )
