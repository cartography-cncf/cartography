from dataclasses import dataclass

from cartography.models.aws.extra_labels import LEGACY_EC2_NETWORK_ACL_RULE
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
from cartography.models.extra_labels import IP_PERMISSION_EGRESS
from cartography.models.extra_labels import IP_PERMISSION_INBOUND


@dataclass(frozen=True)
class EC2NetworkAclRuleNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "Id", description="Unique identifier for this `AWSEC2NetworkAclRule` node."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    network_acl_id: PropertyRef = PropertyRef(
        "NetworkAclId",
        description="Identifier of the network ACL linked to this `AWSEC2NetworkAclRule` node.",
    )
    protocol: PropertyRef = PropertyRef(
        "Protocol",
        description="IP protocol number matched by the network ACL rule.",
    )
    fromport: PropertyRef = PropertyRef(
        "FromPort",
        description="Lowest transport-layer port matched by the network ACL rule.",
    )
    toport: PropertyRef = PropertyRef(
        "ToPort",
        description="Highest transport-layer port matched by the network ACL rule.",
    )
    cidrblock: PropertyRef = PropertyRef(
        "CidrBlock",
        description="IPv4 CIDR range matched by the network ACL rule.",
    )
    ipv6cidrblock: PropertyRef = PropertyRef(
        "Ipv6CidrBlock",
        description="IPv6 CIDR range matched by the network ACL rule.",
    )
    egress: PropertyRef = PropertyRef(
        "Egress",
        description="Whether this `AWSEC2NetworkAclRule` node applies to outbound traffic.",
    )
    rulenumber: PropertyRef = PropertyRef(
        "RuleNumber",
        description="Evaluation order of the network ACL rule.",
    )
    ruleaction: PropertyRef = PropertyRef(
        "RuleAction",
        description="Whether matching traffic is allowed or denied.",
    )
    region: PropertyRef = PropertyRef(
        "Region",
        set_in_kwargs=True,
        description="AWS Region containing this `AWSEC2NetworkAclRule` node.",
    )


@dataclass(frozen=True)
class EC2NetworkAclRuleAclRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EC2NetworkAclRuleToAclRel(CartographyRelSchema):
    target_node_label: str = "AWSEC2NetworkAcl"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"network_acl_id": PropertyRef("NetworkAclId")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MEMBER_OF_NACL"
    properties: EC2NetworkAclRuleAclRelProperties = EC2NetworkAclRuleAclRelProperties()


@dataclass(frozen=True)
class EC2NetworkAclRuleToAWSAccountRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EC2NetworkAclRuleToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: EC2NetworkAclRuleToAWSAccountRelRelProperties = (
        EC2NetworkAclRuleToAWSAccountRelRelProperties()
    )


@dataclass(frozen=True)
class EC2NetworkAclInboundRuleSchema(CartographyNodeSchema):
    """An inbound entry of an AWS [EC2 Network ACL Rule Entry](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_NetworkAclEntry.html). For additional explanation see the [network ACL rules guide](https://docs.aws.amazon.com/vpc/latest/userguide/nacl-rules.html)."""

    label: str = "AWSEC2NetworkAclRule"
    # DEPRECATED: legacy EC2NetworkAclRule node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        [LEGACY_EC2_NETWORK_ACL_RULE, IP_PERMISSION_INBOUND],
    )
    properties: EC2NetworkAclRuleNodeProperties = EC2NetworkAclRuleNodeProperties()
    sub_resource_relationship: EC2NetworkAclRuleToAWSAccountRel = (
        EC2NetworkAclRuleToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            EC2NetworkAclRuleToAclRel(),
        ],
    )


@dataclass(frozen=True)
class EC2NetworkAclEgressRuleSchema(CartographyNodeSchema):
    """An egress entry of an AWS [EC2 Network ACL Rule Entry](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_NetworkAclEntry.html). For additional explanation see the [network ACL rules guide](https://docs.aws.amazon.com/vpc/latest/userguide/nacl-rules.html)."""

    label: str = "AWSEC2NetworkAclRule"
    # DEPRECATED: legacy EC2NetworkAclRule node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        [
            LEGACY_EC2_NETWORK_ACL_RULE,
            IP_PERMISSION_EGRESS,
        ],
    )
    properties: EC2NetworkAclRuleNodeProperties = EC2NetworkAclRuleNodeProperties()
    sub_resource_relationship: EC2NetworkAclRuleToAWSAccountRel = (
        EC2NetworkAclRuleToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            EC2NetworkAclRuleToAclRel(),
        ],
    )
