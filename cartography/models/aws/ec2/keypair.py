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
class EC2KeyPairNodeProperties(CartographyNodeProperties):
    """
    Properties for EC2 keypairs from describe-key-pairs
    """
    id: PropertyRef = PropertyRef('KeyPairArn')
    arn: PropertyRef = PropertyRef('KeyPairArn', extra_index=True)
    keyname: PropertyRef = PropertyRef('KeyName')
    keyfingerprint: PropertyRef = PropertyRef('KeyFingerprint')
    region: PropertyRef = PropertyRef('Region', set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class EC2KeyPairToAwsAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class EC2KeyPairToAWSAccount(CartographyRelSchema):
    """
    Relationship schema for EC2 keypairs to AWS Accounts
    """
    target_node_label: str = 'AWSAccount'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('AWS_ID', set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = 'RESOURCE'
    properties: EC2KeyPairToAwsAccountRelProperties = EC2KeyPairToAwsAccountRelProperties()


@dataclass(frozen=True)
class EC2KeyPairSchema(CartographyNodeSchema):
    """
    Schema for EC2 keypairs from describe-key-pairs
    """
    label: str = 'EC2KeyPair'
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(['KeyPair'])
    properties: EC2KeyPairNodeProperties = EC2KeyPairNodeProperties()
    sub_resource_relationship: EC2KeyPairToAWSAccount = EC2KeyPairToAWSAccount()
