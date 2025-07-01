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
class EfsMountTargetNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("MountTargetId")
    arn: PropertyRef = PropertyRef("MountTargetId", extra_index=True)
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    fileSystem_id: PropertyRef = PropertyRef("FileSystemId")
    lifecycle_state: PropertyRef = PropertyRef("LifeCycleState")
    mount_target_id: PropertyRef = PropertyRef("MountTargetId")
    subnet_id: PropertyRef = PropertyRef("SubnetId")
    availability_zone_id: PropertyRef = PropertyRef("AvailabilityZoneId")
    availability_zone_name: PropertyRef = PropertyRef("AvailabilityZoneName")
    ip_address: PropertyRef = PropertyRef("IpAddress")
    network_interface_id: PropertyRef = PropertyRef("NetworkInterfaceId")
    owner_id: PropertyRef = PropertyRef("OwnerId")
    vpc_id: PropertyRef = PropertyRef("VpcId")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EfsMountTargetToAwsAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EfsMountTargetToAWSAccountRel(CartographyRelSchema):
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
    target_node_label: str = "EfsFileSystem"
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
    label: str = "EfsMountTarget"
    properties: EfsMountTargetNodeProperties = EfsMountTargetNodeProperties()
    sub_resource_relationship: EfsMountTargetToAWSAccountRel = (
        EfsMountTargetToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            EfsMountTargetToEfsFileSystemRel(),
        ]
    )
