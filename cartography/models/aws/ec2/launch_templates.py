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
class LaunchTemplateNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef('LaunchTemplateId')
    launch_template_id: PropertyRef = PropertyRef('LaunchTemplateId')
    name: PropertyRef = PropertyRef('LaunchTemplateName')
    create_time: PropertyRef = PropertyRef('CreateTime')
    created_by: PropertyRef = PropertyRef('CreatedBy')
    default_version_number: PropertyRef = PropertyRef('DefaultVersionNumber')
    latest_version_number: PropertyRef = PropertyRef('LatestVersionNumber')
    region: PropertyRef = PropertyRef('Region', set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class LaunchTemplateToAwsAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class LaunchTemplateToAWSAccount(CartographyRelSchema):
    target_node_label: str = 'AWSAccount'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('AWS_ID', set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: LaunchTemplateToAwsAccountRelProperties = LaunchTemplateToAwsAccountRelProperties()


@dataclass(frozen=True)
class LaunchTemplateSchema(CartographyNodeSchema):
    label: str = 'LaunchTemplate'
    properties: LaunchTemplateNodeProperties = LaunchTemplateNodeProperties()
    sub_resource_relationship: LaunchTemplateToAWSAccount = LaunchTemplateToAWSAccount()
