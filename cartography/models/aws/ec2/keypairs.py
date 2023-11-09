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
class EC2KeyPairNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef('KeyPairArn')
    arn: PropertyRef = PropertyRef('KeyPairArn', extra_index=True)
    keyname: PropertyRef = PropertyRef('KeyName')
    region: PropertyRef = PropertyRef('Region', set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class EC2KeyPairToAwsAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class EC2KeyPairToAWSAccount(CartographyRelSchema):
    target_node_label: str = 'AWSAccount'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('AWS_ID', set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: EC2KeyPairToAwsAccountRelProperties = EC2KeyPairToAwsAccountRelProperties()


@dataclass(frozen=True)
class EC2KeyPairToEC2InstanceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class EC2KeyPairToEC2Instance(CartographyRelSchema):
    target_node_label: str = 'EC2Instance'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('InstanceId')},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "SSH_LOGIN_TO"
    properties: EC2KeyPairToEC2InstanceRelProperties = EC2KeyPairToEC2InstanceRelProperties()


@dataclass(frozen=True)
class EC2KeyPairSchema(CartographyNodeSchema):
    label: str = 'EC2KeyPair'
    properties: EC2KeyPairNodeProperties = EC2KeyPairNodeProperties()
    sub_resource_relationship: EC2KeyPairToAWSAccount = EC2KeyPairToAWSAccount()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            EC2KeyPairToEC2Instance(),
        ],
    )
