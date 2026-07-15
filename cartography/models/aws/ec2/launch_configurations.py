from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class LaunchConfigurationNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "LaunchConfigurationARN", description="The ARN of the launch configuration."
    )
    arn: PropertyRef = PropertyRef(
        "LaunchConfigurationARN", description="The ARN of the launch configuration."
    )
    created_time = PropertyRef("CreatedTime")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )
    image_id: PropertyRef = PropertyRef(
        "ImageId",
        description="The ID of the Amazon Machine Image (AMI) to use to launch your EC2 instances.",
    )
    key_name: PropertyRef = PropertyRef(
        "KeyName", description="The name of the key pair."
    )
    name: PropertyRef = PropertyRef(
        "LaunchConfigurationName",
        extra_index=True,
        description="The name of the launch configuration.",
    )
    security_groups: PropertyRef = PropertyRef(
        "SecurityGroups",
        description="A list that contains the security groups to assign to the instances in the Auto Scaling group.",
    )
    instance_type: PropertyRef = PropertyRef(
        "InstanceType", description="The instance type for the instances."
    )
    kernel_id: PropertyRef = PropertyRef(
        "KernelId", description="The ID of the kernel associated with the AMI."
    )
    ramdisk_id: PropertyRef = PropertyRef(
        "RamdiskId", description="The ID of the RAM disk associated with the AMI."
    )
    instance_monitoring_enabled: PropertyRef = PropertyRef(
        "InstanceMonitoringEnabled",
        description="If true, detailed monitoring is enabled. Otherwise, basic monitoring is enabled.",
    )
    spot_price: PropertyRef = PropertyRef(
        "SpotPrice",
        description="The maximum hourly price to be paid for any Spot Instance launched to fulfill the request.",
    )
    iam_instance_profile: PropertyRef = PropertyRef(
        "IamInstanceProfile",
        description="The name or the Amazon Resource Name (ARN) of the instance profile associated with the IAM role for the instance.",
    )
    ebs_optimized: PropertyRef = PropertyRef(
        "EbsOptimized",
        description="Specifies whether the launch configuration is optimized for EBS I/O (true) or not (false).",
    )
    associate_public_ip_address: PropertyRef = PropertyRef(
        "AssociatePublicIpAddress",
        description="For Auto Scaling groups that are running in a VPC, specifies whether to assign a public IP address to the group's instances.",
    )
    placement_tenancy: PropertyRef = PropertyRef(
        "PlacementTenancy",
        description="The tenancy of the instance, either default or dedicated. An instance with dedicated tenancy runs on isolated, single-tenant hardware and can only be launched into a VPC.",
    )
    region: PropertyRef = PropertyRef(
        "Region",
        set_in_kwargs=True,
        description="The region of the launch configuration.",
    )


@dataclass(frozen=True)
class LaunchConfigurationToAwsAccountRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class LaunchConfigurationToAwsAccountRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSLaunchConfiguration`."

    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: LaunchConfigurationToAwsAccountRelRelProperties = (
        LaunchConfigurationToAwsAccountRelRelProperties()
    )


@dataclass(frozen=True)
class LaunchConfigurationSchema(CartographyNodeSchema):
    "Represents an `AWSLaunchConfiguration` node in the AWS graph."

    label: str = "AWSLaunchConfiguration"
    # DEPRECATED: legacy LaunchConfiguration node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["LaunchConfiguration"])
    properties: LaunchConfigurationNodeProperties = LaunchConfigurationNodeProperties()
    sub_resource_relationship: LaunchConfigurationToAwsAccountRel = (
        LaunchConfigurationToAwsAccountRel()
    )
