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
class EC2KeypairInstanceNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef('KeyPairArn')
    arn: PropertyRef = PropertyRef('KeyPairArn', extra_index=True)
    keyname: PropertyRef = PropertyRef('KeyName')
    region: PropertyRef = PropertyRef('Region', set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class EC2KeypairInstanceToAwsAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class EC2KeypairInstanceToAWSAccount(CartographyRelSchema):
    target_node_label: str = 'AWSAccount'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('AWS_ID', set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: EC2KeypairInstanceToAwsAccountRelProperties = EC2KeypairInstanceToAwsAccountRelProperties()


@dataclass(frozen=True)
class EC2KeypairInstanceToEC2InstanceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class EC2KeypairInstanceToEC2Instance(CartographyRelSchema):
    target_node_label: str = 'EC2Instance'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('InstanceId')},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "SSH_LOGIN_TO"
    properties: EC2KeypairInstanceToEC2InstanceRelProperties = EC2KeypairInstanceToEC2InstanceRelProperties()


@dataclass(frozen=True)
class EC2KeypairInstanceSchema(CartographyNodeSchema):
    """
    EC2 keypairs as known by describe-instances.
    """
    label: str = 'EC2KeyPair'
    properties: EC2KeypairInstanceNodeProperties = EC2KeypairInstanceNodeProperties()
    sub_resource_relationship: EC2KeypairInstanceToAWSAccount = EC2KeypairInstanceToAWSAccount()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            EC2KeypairInstanceToEC2Instance(),
        ],
    )
