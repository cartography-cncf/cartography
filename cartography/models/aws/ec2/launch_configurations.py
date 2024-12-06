from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class LaunchConfigurationNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef('LaunchConfigurationARN')
    arn: PropertyRef = PropertyRef('LaunchConfigurationARN')
    created_time = PropertyRef('CreatedTime')
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)
    image_id: PropertyRef = PropertyRef('ImageId')
    key_name: PropertyRef = PropertyRef('KeyName')
    name: PropertyRef = PropertyRef('LaunchConfigurationName')
    security_groups: PropertyRef = PropertyRef('SecurityGroups')
    instance_type: PropertyRef = PropertyRef('InstanceType')
    kernel_id: PropertyRef = PropertyRef('KernelId')
    ramdisk_id: PropertyRef = PropertyRef('RamdiskId')
    instance_monitoring_enabled: PropertyRef = PropertyRef('InstanceMonitoringEnabled')
    spot_price: PropertyRef = PropertyRef('SpotPrice')
    iam_instance_profile: PropertyRef = PropertyRef('IamInstanceProfile')
    ebs_optimized: PropertyRef = PropertyRef('EbsOptimized')
    associate_public_ip_address: PropertyRef = PropertyRef('AssociatePublicIpAddress')
    placement_tenancy: PropertyRef = PropertyRef('PlacementTenancy')
    region: PropertyRef = PropertyRef('Region', set_in_kwargs=True)


@dataclass(frozen=True)
class LaunchConfigurationToAwsAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class LaunchConfigurationToAwsAccount(CartographyRelSchema):
    target_node_label: str = 'AWSAccount'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('AWS_ID', set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: LaunchConfigurationToAwsAccountRelProperties = LaunchConfigurationToAwsAccountRelProperties()


@dataclass(frozen=True)
class LaunchConfigurationSchema(CartographyNodeSchema):
    label: str = 'LaunchConfiguration'
    properties: LaunchConfigurationNodeProperties = LaunchConfigurationNodeProperties()
    sub_resource_relationship: LaunchConfigurationToAwsAccount = LaunchConfigurationToAwsAccount()
