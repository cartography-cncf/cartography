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
class EfsAccessPointNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "AccessPointArn", description="System-assigned access point ARN"
    )
    arn: PropertyRef = PropertyRef(
        "AccessPointArn",
        extra_index=True,
        description="The unique Amazon Resource Name (ARN) associated with the access point",
    )
    region: PropertyRef = PropertyRef(
        "Region", set_in_kwargs=True, description="The region of the access point"
    )
    access_point_id: PropertyRef = PropertyRef(
        "AccessPointId",
        description="The ID of the access point, assigned by Amazon EFS",
    )
    file_system_id: PropertyRef = PropertyRef(
        "FileSystemId",
        description="The ID of the EFS file system that the access point applies to",
    )
    lifecycle_state: PropertyRef = PropertyRef(
        "LifeCycleState",
        description="Identifies the lifecycle phase of the access point",
    )
    name: PropertyRef = PropertyRef("Name", description="The name of the access point")
    owner_id: PropertyRef = PropertyRef(
        "OwnerId", description="AWS account ID that owns the resource"
    )
    posix_gid: PropertyRef = PropertyRef(
        "Gid",
        description="The POSIX group ID used for all file system operations using this access point",
    )
    posix_uid: PropertyRef = PropertyRef(
        "Uid",
        description="The POSIX user ID used for all file system operations using this access point",
    )
    root_directory_path: PropertyRef = PropertyRef(
        "RootDirectoryPath",
        description="Specifies the path on the EFS file system to expose as the root directory to NFS clients using the access point to access the EFS file system",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )


@dataclass(frozen=True)
class EfsAccessPointToAwsAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EfsAccessPointToAWSAccountRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSEfsAccessPoint`."

    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: EfsAccessPointToAwsAccountRelProperties = (
        EfsAccessPointToAwsAccountRelProperties()
    )


@dataclass(frozen=True)
class EfsAccessPointToEfsFileSystemRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EfsAccessPointToEfsFileSystemRel(CartographyRelSchema):
    "Represents a `ACCESS_POINT_OF` relationship from `AWSEfsAccessPoint` to `AWSEfsFileSystem`."

    target_node_label: str = "AWSEfsFileSystem"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("FileSystemId")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ACCESS_POINT_OF"
    properties: EfsAccessPointToEfsFileSystemRelProperties = (
        EfsAccessPointToEfsFileSystemRelProperties()
    )


@dataclass(frozen=True)
class EfsAccessPointSchema(CartographyNodeSchema):
    "Represents an `AWSEfsAccessPoint` node in the AWS graph."

    label: str = "AWSEfsAccessPoint"
    # DEPRECATED: legacy EfsAccessPoint node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["EfsAccessPoint"])
    properties: EfsAccessPointNodeProperties = EfsAccessPointNodeProperties()
    sub_resource_relationship: EfsAccessPointToAWSAccountRel = (
        EfsAccessPointToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            EfsAccessPointToEfsFileSystemRel(),
        ]
    )
