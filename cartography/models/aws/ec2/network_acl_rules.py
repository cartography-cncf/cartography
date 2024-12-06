from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class EC2NetworkAclRuleNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef('Id')
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)
    network_acl_id: PropertyRef = PropertyRef('NetworkAclId')
    protocol: PropertyRef = PropertyRef('Protocol')
    fromport: PropertyRef = PropertyRef('FromPort')
    toport: PropertyRef = PropertyRef('ToPort')
    cidrblock: PropertyRef = PropertyRef('CidrBlock')
    ipv6cidrblock: PropertyRef = PropertyRef('Ipv6CidrBlock')
    egress: PropertyRef = PropertyRef('Egress')
    rulenumber: PropertyRef = PropertyRef('RuleNumber')
    ruleaction: PropertyRef = PropertyRef('RuleAction')
    region: PropertyRef = PropertyRef('Region', set_in_kwargs=True)


@dataclass(frozen=True)
class EC2NetworkAclRuleAclRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class EC2NetworkAclRuleToAcl(CartographyRelSchema):
    target_node_label: str = 'EC2NetworkAcl'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'network_acl_id': PropertyRef('NetworkAclId')},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MEMBER_OF_NACL"
    properties: EC2NetworkAclRuleAclRelProperties = EC2NetworkAclRuleAclRelProperties()


@dataclass(frozen=True)
class EC2NetworkAclRuleToAwsAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class EC2NetworkAclRuleToAWSAccount(CartographyRelSchema):
    target_node_label: str = 'AWSAccount'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('AWS_ID', set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: EC2NetworkAclRuleToAwsAccountRelProperties = EC2NetworkAclRuleToAwsAccountRelProperties()


@dataclass(frozen=True)
class EC2NetworkAclInboundRuleSchema(CartographyNodeSchema):
    """
    Network interface as known by describe-network-interfaces.
    """
    label: str = 'EC2NetworkAclRule'
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        ['IpPermissionInbound'],
    )
    properties: EC2NetworkAclRuleNodeProperties = EC2NetworkAclRuleNodeProperties()
    sub_resource_relationship: EC2NetworkAclRuleToAWSAccount = EC2NetworkAclRuleToAWSAccount()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            EC2NetworkAclRuleToAcl(),
        ],
    )


@dataclass(frozen=True)
class EC2NetworkAclEgressRuleSchema(CartographyNodeSchema):
    """
    Network interface as known by describe-network-interfaces.
    """
    label: str = 'EC2NetworkAclRule'
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        [
            'IpPermissionEgress',
        ],
    )
    properties: EC2NetworkAclRuleNodeProperties = EC2NetworkAclRuleNodeProperties()
    sub_resource_relationship: EC2NetworkAclRuleToAWSAccount = EC2NetworkAclRuleToAWSAccount()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            EC2NetworkAclRuleToAcl(),
        ],
    )
