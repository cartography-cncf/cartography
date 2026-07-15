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
    id: PropertyRef = PropertyRef(
        "Id", description="Unique identifier for this `AWSEC2NetworkAclRule` node."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that updated this `AWSEC2NetworkAclRule` node.",
    )
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
    "Represents a `MEMBER_OF_NACL` relationship from `AWSEC2NetworkAclRule` to `AWSEC2NetworkAcl`."

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
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSEC2NetworkAclRule`."

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
    """
    Network interface as known by describe-network-interfaces.
    """

    label: str = "AWSEC2NetworkAclRule"
    # DEPRECATED: legacy EC2NetworkAclRule node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        ["EC2NetworkAclRule", "IpPermissionInbound"],
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
    """
    Network interface as known by describe-network-interfaces.
    """

    label: str = "AWSEC2NetworkAclRule"
    # DEPRECATED: legacy EC2NetworkAclRule node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        [
            "EC2NetworkAclRule",
            "IpPermissionEgress",
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
