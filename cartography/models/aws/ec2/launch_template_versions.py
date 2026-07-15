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
class LaunchTemplateVersionNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "Id", description="The ID of the launch template version (ID-version)."
    )
    name: PropertyRef = PropertyRef(
        "LaunchTemplateName", description="The name of the launch template."
    )
    create_time: PropertyRef = PropertyRef(
        "CreateTime", description="The time the version was created."
    )
    created_by: PropertyRef = PropertyRef(
        "CreatedBy", description="The principal that created the version."
    )
    default_version: PropertyRef = PropertyRef(
        "DefaultVersion",
        description="Indicates whether the version is the default version.",
    )
    version_number: PropertyRef = PropertyRef(
        "VersionNumber", description="The version number."
    )
    version_description: PropertyRef = PropertyRef(
        "VersionDescription", description="The description of the version."
    )
    kernel_id: PropertyRef = PropertyRef(
        "KernelId", description="The ID of the kernel, if applicable."
    )
    ebs_optimized: PropertyRef = PropertyRef(
        "EbsOptimized",
        description="Indicates whether the instance is optimized for Amazon EBS I/O.",
    )
    iam_instance_profile_arn: PropertyRef = PropertyRef(
        "IamInstanceProfileArn",
        description="The Amazon Resource Name (ARN) of the instance profile.",
    )
    iam_instance_profile_name: PropertyRef = PropertyRef(
        "IamInstanceProfileName", description="The name of the instance profile."
    )
    image_id: PropertyRef = PropertyRef(
        "ImageId", description="The ID of the AMI that was used to launch the instance."
    )
    instance_type: PropertyRef = PropertyRef(
        "InstanceType", description="The instance type."
    )
    key_name: PropertyRef = PropertyRef(
        "KeyName", description="The name of the key pair."
    )
    monitoring_enabled: PropertyRef = PropertyRef(
        "MonitoringEnabled",
        description="Indicates whether detailed monitoring is enabled. Otherwise, basic monitoring is enabled.",
    )
    ramdisk_id: PropertyRef = PropertyRef(
        "RamdiskId", description="The ID of the RAM disk, if applicable."
    )
    disable_api_termination: PropertyRef = PropertyRef(
        "DisableApiTermination",
        description="If set to true, indicates that the instance cannot be terminated using the Amazon EC2 console, command line tool, or API.",
    )
    instance_initiated_shutdown_behavior: PropertyRef = PropertyRef(
        "InstanceInitiatedShutdownBehavior",
        description="Indicates whether an instance stops or terminates when you initiate shutdown from the instance (using the operating system command for system shutdown).",
    )
    security_group_ids: PropertyRef = PropertyRef(
        "SecurityGroupIds", description="The security group IDs."
    )
    security_groups: PropertyRef = PropertyRef(
        "SecurityGroups", description="The security group names."
    )
    region: PropertyRef = PropertyRef(
        "Region", set_in_kwargs=True, description="The region of the launch template."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )


@dataclass(frozen=True)
class LaunchTemplateVersionToAWSAccountRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class LaunchTemplateVersionToAWSAccountRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSLaunchTemplateVersion`."

    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: LaunchTemplateVersionToAWSAccountRelRelProperties = (
        LaunchTemplateVersionToAWSAccountRelRelProperties()
    )


@dataclass(frozen=True)
class LaunchTemplateVersionToLTRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class LaunchTemplateVersionToLTRel(CartographyRelSchema):
    "Represents a `VERSION` relationship from `AWSLaunchTemplate` to `AWSLaunchTemplateVersion`."

    target_node_label: str = "AWSLaunchTemplate"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("LaunchTemplateId")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "VERSION"
    properties: LaunchTemplateVersionToLTRelRelProperties = (
        LaunchTemplateVersionToLTRelRelProperties()
    )


@dataclass(frozen=True)
class LaunchTemplateVersionSchema(CartographyNodeSchema):
    "Represents an `AWSLaunchTemplateVersion` node in the AWS graph."

    label: str = "AWSLaunchTemplateVersion"
    # DEPRECATED: legacy LaunchTemplateVersion node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["LaunchTemplateVersion"])
    properties: LaunchTemplateVersionNodeProperties = (
        LaunchTemplateVersionNodeProperties()
    )
    sub_resource_relationship: LaunchTemplateVersionToAWSAccountRel = (
        LaunchTemplateVersionToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            LaunchTemplateVersionToLTRel(),
        ],
    )
