from dataclasses import dataclass

from cartography.models.aws.ec2.instances import EC2InstanceToAWSAccount
from cartography.models.aws.ec2.subnet_instance import EC2SubnetToAWSAccount
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
    arn: PropertyRef = PropertyRef('AutoScalingGroupARN')
    capacityrebalance: PropertyRef = PropertyRef('CapacityRebalance')
    createdtime: PropertyRef = PropertyRef('CreatedTime')
    defaultcooldown: PropertyRef = PropertyRef('DefaultCooldown')
    desiredcapacity: PropertyRef = PropertyRef('DesiredCapacity')
    healthcheckgraceperiod: PropertyRef = PropertyRef('HealthCheckGracePeriod')
    healthchecktype: PropertyRef = PropertyRef('HealthCheckType')
    launchconfigurationname: PropertyRef = PropertyRef('LaunchConfigurationName')
    launchtemplatename: PropertyRef = PropertyRef('LaunchTemplateName')
    launchtemplateid: PropertyRef = PropertyRef('LaunchTemplateId')
    launchtemplateversion: PropertyRef = PropertyRef('LaunchTemplateVersion')
    maxinstancelifetime: PropertyRef = PropertyRef('MaxInstanceLifetime')
    maxsize: PropertyRef = PropertyRef('MaxSize')
    minsize: PropertyRef = PropertyRef('MinSize')
    name: PropertyRef = PropertyRef('AutoScalingGroupName')
    newinstancesprotectedfromscalein: PropertyRef = PropertyRef('NewInstancesProtectedFromScaleIn')
    region: PropertyRef = PropertyRef('Region', set_in_kwargs=True)
    status: PropertyRef = PropertyRef('Status')
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class EC2SubnetAutoScalingGroupNodeProperties(CartographyNodeProperties):
    subnetid: PropertyRef = PropertyRef('VPCZoneIdentifier')
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class EC2InstanceAutoScalingGroupNodeProperties(CartographyNodeProperties):
    instanceid: PropertyRef = PropertyRef('InstanceId')
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class AutoScalingGroupToEC2SubnetRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class AutoScalingGroupToEC2InstanceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class AutoScalingGroupToAwsAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class AutoScalingGroupToLaunchTemplateRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class AutoScalingGroupToLaunchConfigurationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class AutoScalingGroupToEC2Subnet(CartographyRelSchema):
    target_node_label: str = 'EC2Subnet'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'subnetid': PropertyRef('VPCZoneIdentifier')},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "VPC_IDENTIFIER"
    properties: AutoScalingGroupToEC2SubnetRelProperties = AutoScalingGroupToEC2SubnetRelProperties()


@dataclass(frozen=True)
class AutoScalingGroupToEC2Instance(CartographyRelSchema):
    target_node_label: str = 'EC2Instance'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('InstanceId')},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "MEMBER_AUTO_SCALE_GROUP"
    properties: AutoScalingGroupToEC2InstanceRelProperties = AutoScalingGroupToEC2InstanceRelProperties()


@dataclass(frozen=True)
class AutoScalingGroupToAWSAccount(CartographyRelSchema):
    target_node_label: str = 'AWSAccount'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('AWS_ID', set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AutoScalingGroupToAwsAccountRelProperties = AutoScalingGroupToAwsAccountRelProperties()


@dataclass(frozen=True)
class AutoScalingGroupToLaunchTemplate(CartographyRelSchema):
    target_node_label: str = 'LaunchTemplate'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('LaunchTemplateId')},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_LAUNCH_TEMPLATE"
    properties: AutoScalingGroupToLaunchTemplateRelProperties = AutoScalingGroupToLaunchTemplateRelProperties()


@dataclass(frozen=True)
class AutoScalingGroupToLaunchConfiguration(CartographyRelSchema):
    target_node_label: str = 'LaunchConfiguration'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'name': PropertyRef('LaunchConfigurationName')},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_LAUNCH_CONFIG"
    properties: AutoScalingGroupToLaunchConfigurationRelProperties = (
        AutoScalingGroupToLaunchConfigurationRelProperties()
    )


@dataclass(frozen=True)
class EC2SubnetAutoScalingGroupSchema(CartographyNodeSchema):
    label: str = 'EC2Subnet'
    properties: EC2SubnetAutoScalingGroupNodeProperties = EC2SubnetAutoScalingGroupNodeProperties()
    sub_resource_relationship: EC2SubnetToAWSAccount = EC2SubnetToAWSAccount()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AutoScalingGroupToEC2Subnet(),
        ],
    )


@dataclass(frozen=True)
class EC2InstanceAutoScalingGroupSchema(CartographyNodeSchema):
    label: str = 'EC2Instance'
    properties: EC2InstanceAutoScalingGroupNodeProperties = EC2InstanceAutoScalingGroupNodeProperties()
    sub_resource_relationship: EC2InstanceToAWSAccount = EC2InstanceToAWSAccount()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AutoScalingGroupToEC2Instance(),
        ],
    )


@dataclass(frozen=True)
class AutoScalingGroupSchema(CartographyNodeSchema):
    label: str = 'AutoScalingGroup'
    properties: AutoScalingGroupNodeProperties = AutoScalingGroupNodeProperties()
    sub_resource_relationship: AutoScalingGroupToAWSAccount = AutoScalingGroupToAWSAccount()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AutoScalingGroupToEC2Subnet(),
            AutoScalingGroupToEC2Instance(),
            AutoScalingGroupToLaunchTemplate(),
            AutoScalingGroupToLaunchConfiguration(),
        ],
    )
