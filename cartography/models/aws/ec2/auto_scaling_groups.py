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
class AutoScalingGroupNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("AutoScalingGroupARN")
    arn: PropertyRef = PropertyRef("AutoScalingGroupARN")
    capacityrebalance: PropertyRef = PropertyRef("CapacityRebalance")
    createdtime: PropertyRef = PropertyRef("CreatedTime")
    defaultcooldown: PropertyRef = PropertyRef("DefaultCooldown")
    desiredcapacity: PropertyRef = PropertyRef("DesiredCapacity")
    healthcheckgraceperiod: PropertyRef = PropertyRef("HealthCheckGracePeriod")
    healthchecktype: PropertyRef = PropertyRef("HealthCheckType")
    launchconfigurationname: PropertyRef = PropertyRef("LaunchConfigurationName")
    launchtemplatename: PropertyRef = PropertyRef("LaunchTemplateName")
    launchtemplateid: PropertyRef = PropertyRef("LaunchTemplateId")
    launchtemplateversion: PropertyRef = PropertyRef("LaunchTemplateVersion")
    maxinstancelifetime: PropertyRef = PropertyRef("MaxInstanceLifetime")
    maxsize: PropertyRef = PropertyRef("MaxSize")
    minsize: PropertyRef = PropertyRef("MinSize")
    name: PropertyRef = PropertyRef("AutoScalingGroupName")
    newinstancesprotectedfromscalein: PropertyRef = PropertyRef(
        "NewInstancesProtectedFromScaleIn",
    )
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    status: PropertyRef = PropertyRef("Status")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# EC2 to AutoScalingGroup
@dataclass(frozen=True)
class EC2InstanceToAWSAccountRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EC2InstanceToAWSAccountRel(CartographyRelSchema):
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
    target_node_label: str = "AutoScalingGroup"
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
    id: PropertyRef = PropertyRef("InstanceId")
    instanceid: PropertyRef = PropertyRef("InstanceId", extra_index=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)


@dataclass(frozen=True)
class EC2InstanceAutoScalingGroupSchema(CartographyNodeSchema):
    label: str = "EC2Instance"
    properties: EC2InstanceAutoScalingGroupProperties = (
        EC2InstanceAutoScalingGroupProperties()
    )
    sub_resource_relationship: EC2InstanceToAWSAccountRel = EC2InstanceToAWSAccountRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            EC2InstanceToAutoScalingGroupRel(),
        ],
    )


# EC2Subnet to AutoScalingGroup
@dataclass(frozen=True)
class EC2SubnetToAWSAccountRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EC2SubnetToAWSAccountRel(CartographyRelSchema):
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
    target_node_label: str = "AutoScalingGroup"
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
    id: PropertyRef = PropertyRef("VPCZoneIdentifier")
    subnetid: PropertyRef = PropertyRef("VPCZoneIdentifier", extra_index=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EC2SubnetAutoScalingGroupSchema(CartographyNodeSchema):
    label: str = "EC2Subnet"
    properties: EC2SubnetAutoScalingGroupNodeProperties = (
        EC2SubnetAutoScalingGroupNodeProperties()
    )
    sub_resource_relationship: EC2SubnetToAWSAccountRel = EC2SubnetToAWSAccountRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            EC2SubnetToAutoScalingGroupRel(),
        ],
    )


# AutoScalingGroup
@dataclass(frozen=True)
class AutoScalingGroupToAWSAccountRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AutoScalingGroupToAWSAccountRel(CartographyRelSchema):
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
    target_node_label: str = "LaunchTemplate"
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
    target_node_label: str = "LaunchConfiguration"
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
    label: str = "AutoScalingGroup"
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
