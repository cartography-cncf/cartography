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
class EfsAccessPointNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("AccessPointArn")
    arn: PropertyRef = PropertyRef("AccessPointArn", extra_index=True)
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    access_point_id: PropertyRef = PropertyRef("AccessPointId")
    file_system_id: PropertyRef = PropertyRef("FileSystemId")
    lifecycle_state: PropertyRef = PropertyRef("LifeCycleState")
    name: PropertyRef = PropertyRef("Name")
    owner_id: PropertyRef = PropertyRef("OwnerId")
    posix_gid: PropertyRef = PropertyRef("Gid")
    posix_uid: PropertyRef = PropertyRef("Uid")
    root_directory_path: PropertyRef = PropertyRef("RootDirectoryPath")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EfsAccessPointToAwsAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EfsAccessPointToAWSAccountRel(CartographyRelSchema):
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
    target_node_label: str = "EfsFileSystem"
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
    label: str = "EfsAccessPoint"
    properties: EfsAccessPointNodeProperties = EfsAccessPointNodeProperties()
    sub_resource_relationship: EfsAccessPointToAWSAccountRel = (
        EfsAccessPointToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            EfsAccessPointToEfsFileSystemRel(),
        ]
    )
