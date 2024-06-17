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
class LaunchTemplateVersionNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef('Id')
    name: PropertyRef = PropertyRef('LaunchTemplateName')
    create_time: PropertyRef = PropertyRef('CreateTime')
    created_by: PropertyRef = PropertyRef('CreatedBy')
    default_version: PropertyRef = PropertyRef('DefaultVersion')
    version_number: PropertyRef = PropertyRef('VersionNumber')
    version_description: PropertyRef = PropertyRef('VersionDescription')
    kernel_id: PropertyRef = PropertyRef('KernelId')
    ebs_optimized: PropertyRef = PropertyRef('EbsOptimized')
    iam_instance_profile_arn: PropertyRef = PropertyRef('IamInstanceProfileArn')
    iam_instance_profile_name: PropertyRef = PropertyRef('IamInstanceProfileName')
    image_id: PropertyRef = PropertyRef('ImageId')
    instance_type: PropertyRef = PropertyRef('InstanceType')
    key_name: PropertyRef = PropertyRef('KeyName')
    monitoring_enabled: PropertyRef = PropertyRef('MonitoringEnabled')
    ramdisk_id: PropertyRef = PropertyRef('RamdiskId')
    disable_api_termination: PropertyRef = PropertyRef('DisableApiTermination')
    instance_initiated_shutdown_behavior: PropertyRef = PropertyRef('InstanceInitiatedShutdownBehavior')
    security_group_ids: PropertyRef = PropertyRef('SecurityGroupIds')
    security_groups: PropertyRef = PropertyRef('SecurityGroups')
    region: PropertyRef = PropertyRef('Region', set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class LaunchTemplateVersionToAwsAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class LaunchTemplateVersionToAWSAccount(CartographyRelSchema):
    target_node_label: str = 'AWSAccount'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('AWS_ID', set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: LaunchTemplateVersionToAwsAccountRelProperties = LaunchTemplateVersionToAwsAccountRelProperties()


@dataclass(frozen=True)
class LaunchTemplateVersionToLTRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class LaunchTemplateVersionToLT(CartographyRelSchema):
    target_node_label: str = 'LaunchTemplate'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('LaunchTemplateId')},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "VERSION"
    properties: LaunchTemplateVersionToLTRelProperties = LaunchTemplateVersionToLTRelProperties()


@dataclass(frozen=True)
class LaunchTemplateVersionSchema(CartographyNodeSchema):
    label: str = 'LaunchTemplateVersion'
    properties: LaunchTemplateVersionNodeProperties = LaunchTemplateVersionNodeProperties()
    sub_resource_relationship: LaunchTemplateVersionToAWSAccount = LaunchTemplateVersionToAWSAccount()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            LaunchTemplateVersionToLT(),
        ],
    )
