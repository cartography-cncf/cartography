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
    id: PropertyRef = PropertyRef('AutoScalingGroupARN')
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


# EC2 to AutoScalingGroup
@dataclass(frozen=True)
class EC2InstanceToAwsAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class EC2InstanceToAWSAccount(CartographyRelSchema):
    target_node_label: str = 'AWSAccount'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('AWS_ID', set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: EC2InstanceToAwsAccountRelProperties = EC2InstanceToAwsAccountRelProperties()


@dataclass(frozen=True)
class EC2InstanceToAutoScalingGroupRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class EC2InstanceToAutoScalingGroup(CartographyRelSchema):
    target_node_label: str = 'AutoScalingGroup'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('AutoScalingGroupARN')},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MEMBER_AUTO_SCALE_GROUP"
    properties: EC2InstanceToAutoScalingGroupRelProperties = EC2InstanceToAutoScalingGroupRelProperties()


@dataclass(frozen=True)
class EC2InstanceAutoScalingGroupProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef('InstanceId')
    instanceid: PropertyRef = PropertyRef('InstanceId', extra_index=True)
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)
    region: PropertyRef = PropertyRef('Region', set_in_kwargs=True)


@dataclass(frozen=True)
class EC2InstanceAutoScalingGroupSchema(CartographyNodeSchema):
    label: str = 'EC2Instance'
    properties: EC2InstanceAutoScalingGroupProperties = EC2InstanceAutoScalingGroupProperties()
    sub_resource_relationship: EC2InstanceToAWSAccount = EC2InstanceToAWSAccount()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            EC2InstanceToAutoScalingGroup(),
        ],
    )


# EC2Subnet to AutoScalingGroup
@dataclass(frozen=True)
class EC2SubnetToAwsAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class EC2SubnetToAWSAccount(CartographyRelSchema):
    target_node_label: str = 'AWSAccount'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('AWS_ID', set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: EC2SubnetToAwsAccountRelProperties = EC2SubnetToAwsAccountRelProperties()


@dataclass(frozen=True)
class EC2SubnetToAutoScalingGroupRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class EC2SubnetToAutoScalingGroup(CartographyRelSchema):
    target_node_label: str = 'AutoScalingGroup'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('AutoScalingGroupARN')},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "VPC_IDENTIFIER"
    properties: EC2SubnetToAutoScalingGroupRelProperties = EC2SubnetToAutoScalingGroupRelProperties()


@dataclass(frozen=True)
class EC2SubnetAutoScalingGroupNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef('VPCZoneIdentifier')
    subnetid: PropertyRef = PropertyRef('VPCZoneIdentifier', extra_index=True)
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class EC2SubnetAutoScalingGroupSchema(CartographyNodeSchema):
    label: str = 'EC2Subnet'
    properties: EC2SubnetAutoScalingGroupNodeProperties = EC2SubnetAutoScalingGroupNodeProperties()
    sub_resource_relationship: EC2SubnetToAWSAccount = EC2SubnetToAWSAccount()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            EC2SubnetToAutoScalingGroup(),
        ],
    )


# AutoScalingGroup
@dataclass(frozen=True)
class AutoScalingGroupToAwsAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


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
class AutoScalingGroupToLaunchTemplateRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


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
class AutoScalingGroupToLaunchConfigurationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


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
class AutoScalingGroupSchema(CartographyNodeSchema):
    label: str = 'AutoScalingGroup'
    properties: AutoScalingGroupNodeProperties = AutoScalingGroupNodeProperties()
    sub_resource_relationship: AutoScalingGroupToAWSAccount = AutoScalingGroupToAWSAccount()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AutoScalingGroupToLaunchTemplate(),
            AutoScalingGroupToLaunchConfiguration(),
        ],
    )
