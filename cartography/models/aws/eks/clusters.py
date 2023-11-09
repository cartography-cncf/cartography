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
class EKSClusterNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef('arn')
    arn: PropertyRef = PropertyRef('arn', extra_index=True)
    name: PropertyRef = PropertyRef('name', extra_index=True)
    region: PropertyRef = PropertyRef('Region', set_in_kwargs=True)
    created_at: PropertyRef = PropertyRef('created_at')
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)
    endpoint: PropertyRef = PropertyRef('endpoint')
    endpoint_public_access: PropertyRef = PropertyRef('ClusterEndpointPublic')
    rolearn: PropertyRef = PropertyRef('roleArn')
    version: PropertyRef = PropertyRef('version')
    platform_version: PropertyRef = PropertyRef('platformVersion')
    status: PropertyRef = PropertyRef('status')
    audit_logging: PropertyRef = PropertyRef('ClusterLogging')


@dataclass(frozen=True)
class EKSClusterToAwsAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class EKSClusterToAWSAccount(CartographyRelSchema):
    target_node_label: str = 'AWSAccount'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('AWS_ID', set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: EKSClusterToAwsAccountRelProperties = EKSClusterToAwsAccountRelProperties()


@dataclass(frozen=True)
class EKSClusterSchema(CartographyNodeSchema):
    label: str = 'EKSCluster'
    properties: EKSClusterNodeProperties = EKSClusterNodeProperties()
    sub_resource_relationship: EKSClusterToAWSAccount = EKSClusterToAWSAccount()
