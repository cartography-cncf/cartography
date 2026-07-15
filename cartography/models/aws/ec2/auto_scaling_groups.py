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
class AutoScalingGroupNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "AutoScalingGroupARN",
        description="The ARN of the Auto Scaling Group (same as arn)",
    )
    arn: PropertyRef = PropertyRef(
        "AutoScalingGroupARN", description="The ARN of the Auto Scaling Group"
    )
    capacityrebalance: PropertyRef = PropertyRef(
        "CapacityRebalance",
        description="Indicates whether Capacity Rebalancing is enabled.",
    )
    createdtime: PropertyRef = PropertyRef(
        "CreatedTime", description="The date and time the group was created."
    )
    defaultcooldown: PropertyRef = PropertyRef(
        "DefaultCooldown",
        description="The duration of the default cooldown period, in seconds.",
    )
    desiredcapacity: PropertyRef = PropertyRef(
        "DesiredCapacity", description="The desired size of the group."
    )
    healthcheckgraceperiod: PropertyRef = PropertyRef(
        "HealthCheckGracePeriod",
        description="The amount of time, in seconds, that Amazon EC2 Auto Scaling waits before checking the health status of an EC2 instance that has come into service.",
    )
    healthchecktype: PropertyRef = PropertyRef(
        "HealthCheckType", description="The service to use for the health checks."
    )
    launchconfigurationname: PropertyRef = PropertyRef(
        "LaunchConfigurationName",
        description="The name of the associated launch configuration.",
    )
    launchtemplatename: PropertyRef = PropertyRef(
        "LaunchTemplateName", description="The name of the launch template."
    )
    launchtemplateid: PropertyRef = PropertyRef(
        "LaunchTemplateId", description="The ID of the launch template."
    )
    launchtemplateversion: PropertyRef = PropertyRef(
        "LaunchTemplateVersion",
        description="The version number of the launch template.",
    )
    maxinstancelifetime: PropertyRef = PropertyRef(
        "MaxInstanceLifetime",
        description="The maximum amount of time, in seconds, that an instance can be in service.",
    )
    maxsize: PropertyRef = PropertyRef(
        "MaxSize", description="The maximum size of the group."
    )
    minsize: PropertyRef = PropertyRef(
        "MinSize", description="The minimum size of the group."
    )
    name: PropertyRef = PropertyRef(
        "AutoScalingGroupName", description="The name of the Auto Scaling group"
    )
    newinstancesprotectedfromscalein: PropertyRef = PropertyRef(
        "NewInstancesProtectedFromScaleIn",
        description="Indicates whether newly launched instances are protected from termination by Amazon EC2 Auto Scaling when scaling in.",
    )
    region: PropertyRef = PropertyRef(
        "Region",
        set_in_kwargs=True,
        description="The region of the auto scaling group.",
    )
    status: PropertyRef = PropertyRef(
        "Status",
        description="The current state of the group when the DeleteAutoScalingGroup operation is in progress.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )


# EC2 to AWSAutoScalingGroup
@dataclass(frozen=True)
class EC2InstanceToAWSAccountRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EC2InstanceToAWSAccountRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSEC2Instance`."

    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: EC2InstanceToAWSAccountRelRelProperties = (
        EC2InstanceToAWSAccountRelRelProperties()
    )


@dataclass(frozen=True)
class EC2InstanceToAutoScalingGroupRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EC2InstanceToAutoScalingGroupRel(CartographyRelSchema):
    "Represents a `MEMBER_AUTO_SCALE_GROUP` relationship from `AWSEC2Instance` to `AWSAutoScalingGroup`."

    target_node_label: str = "AWSAutoScalingGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AutoScalingGroupARN")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MEMBER_AUTO_SCALE_GROUP"
    properties: EC2InstanceToAutoScalingGroupRelRelProperties = (
        EC2InstanceToAutoScalingGroupRelRelProperties()
    )


@dataclass(frozen=True)
class EC2InstanceAutoScalingGroupProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "InstanceId", description="Same as `instanceid` below."
    )
    instanceid: PropertyRef = PropertyRef(
        "InstanceId",
        extra_index=True,
        description="The instance id provided by AWS.  This is [globally unique](https://forums.aws.amazon.com/thread.jspa?threadID=137203)",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )
    region: PropertyRef = PropertyRef(
        "Region",
        set_in_kwargs=True,
        description="The AWS region this Instance is running in",
    )


@dataclass(frozen=True)
class EC2InstanceAutoScalingGroupSchema(CartographyNodeSchema):
    "Represents an `AWSEC2Instance` node in the AWS graph."

    label: str = "AWSEC2Instance"
    # DEPRECATED: legacy EC2Instance node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["EC2Instance"])
    properties: EC2InstanceAutoScalingGroupProperties = (
        EC2InstanceAutoScalingGroupProperties()
    )
    sub_resource_relationship: EC2InstanceToAWSAccountRel = EC2InstanceToAWSAccountRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            EC2InstanceToAutoScalingGroupRel(),
        ],
    )


# AWSEC2Subnet to AWSAutoScalingGroup
@dataclass(frozen=True)
class EC2SubnetToAWSAccountRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EC2SubnetToAWSAccountRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSEC2Subnet`."

    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: EC2SubnetToAWSAccountRelRelProperties = (
        EC2SubnetToAWSAccountRelRelProperties()
    )


@dataclass(frozen=True)
class EC2SubnetToAutoScalingGroupRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EC2SubnetToAutoScalingGroupRel(CartographyRelSchema):
    "Represents a `VPC_IDENTIFIER` relationship from `AWSAutoScalingGroup` to `AWSEC2Subnet`."

    target_node_label: str = "AWSAutoScalingGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AutoScalingGroupARN")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "VPC_IDENTIFIER"
    properties: EC2SubnetToAutoScalingGroupRelRelProperties = (
        EC2SubnetToAutoScalingGroupRelRelProperties()
    )


@dataclass(frozen=True)
class EC2SubnetAutoScalingGroupNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("VPCZoneIdentifier", description="same as subnetid")
    subnetid: PropertyRef = PropertyRef(
        "VPCZoneIdentifier", extra_index=True, description="The ID of the subnet"
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )


@dataclass(frozen=True)
class EC2SubnetAutoScalingGroupSchema(CartographyNodeSchema):
    "Represents a subnet in an Amazon EC2 virtual private cloud."

    label: str = "AWSEC2Subnet"
    properties: EC2SubnetAutoScalingGroupNodeProperties = (
        EC2SubnetAutoScalingGroupNodeProperties()
    )
    # DEPRECATED: legacy EC2Subnet node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["EC2Subnet", "Subnet"])
    sub_resource_relationship: EC2SubnetToAWSAccountRel = EC2SubnetToAWSAccountRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            EC2SubnetToAutoScalingGroupRel(),
        ],
    )


# AWSAutoScalingGroup
@dataclass(frozen=True)
class AutoScalingGroupToAWSAccountRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AutoScalingGroupToAWSAccountRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSAutoScalingGroup`."

    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AutoScalingGroupToAWSAccountRelRelProperties = (
        AutoScalingGroupToAWSAccountRelRelProperties()
    )


@dataclass(frozen=True)
class AutoScalingGroupToLaunchTemplateRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AutoScalingGroupToLaunchTemplateRel(CartographyRelSchema):
    "Represents a `HAS_LAUNCH_TEMPLATE` relationship from `AWSAutoScalingGroup` to `AWSLaunchTemplate`."

    target_node_label: str = "AWSLaunchTemplate"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("LaunchTemplateId")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_LAUNCH_TEMPLATE"
    properties: AutoScalingGroupToLaunchTemplateRelRelProperties = (
        AutoScalingGroupToLaunchTemplateRelRelProperties()
    )


@dataclass(frozen=True)
class AutoScalingGroupToLaunchConfigurationRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AutoScalingGroupToLaunchConfigurationRel(CartographyRelSchema):
    "Represents a `HAS_LAUNCH_CONFIG` relationship from `AWSAutoScalingGroup` to `AWSLaunchConfiguration`."

    target_node_label: str = "AWSLaunchConfiguration"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"name": PropertyRef("LaunchConfigurationName")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_LAUNCH_CONFIG"
    properties: AutoScalingGroupToLaunchConfigurationRelRelProperties = (
        AutoScalingGroupToLaunchConfigurationRelRelProperties()
    )


@dataclass(frozen=True)
class AutoScalingGroupSchema(CartographyNodeSchema):
    "Represents an `AWSAutoScalingGroup` node in the AWS graph."

    label: str = "AWSAutoScalingGroup"
    # DEPRECATED: legacy AutoScalingGroup node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["AutoScalingGroup"])
    properties: AutoScalingGroupNodeProperties = AutoScalingGroupNodeProperties()
    sub_resource_relationship: AutoScalingGroupToAWSAccountRel = (
        AutoScalingGroupToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AutoScalingGroupToLaunchTemplateRel(),
            AutoScalingGroupToLaunchConfigurationRel(),
        ],
    )
