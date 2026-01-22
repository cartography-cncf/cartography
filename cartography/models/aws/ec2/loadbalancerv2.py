from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_source_node_matcher
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import SourceNodeMatcher
from cartography.models.core.relationships import TargetNodeMatcher

# LoadBalancerV2 Schema


@dataclass(frozen=True)
class LoadBalancerV2NodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("DNSName")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("LoadBalancerName")
    dnsname: PropertyRef = PropertyRef("DNSName", extra_index=True)
    canonicalhostedzonenameid: PropertyRef = PropertyRef("CanonicalHostedZoneId")
    type: PropertyRef = PropertyRef("Type")
    scheme: PropertyRef = PropertyRef("Scheme")
    arn: PropertyRef = PropertyRef("LoadBalancerArn", extra_index=True)
    createdtime: PropertyRef = PropertyRef("CreatedTime")


@dataclass(frozen=True)
class LoadBalancerV2ToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class LoadBalancerV2ToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: LoadBalancerV2ToAWSAccountRelProperties = (
        LoadBalancerV2ToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class LoadBalancerV2ToEC2SecurityGroupRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class LoadBalancerV2ToEC2SecurityGroupRel(CartographyRelSchema):
    target_node_label: str = "EC2SecurityGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"groupid": PropertyRef("SecurityGroupIds", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MEMBER_OF_EC2_SECURITY_GROUP"
    properties: LoadBalancerV2ToEC2SecurityGroupRelProperties = (
        LoadBalancerV2ToEC2SecurityGroupRelProperties()
    )


@dataclass(frozen=True)
class LoadBalancerV2ToEC2SubnetRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class LoadBalancerV2ToEC2SubnetRel(CartographyRelSchema):
    target_node_label: str = "EC2Subnet"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"subnetid": PropertyRef("SubnetIds", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "SUBNET"
    properties: LoadBalancerV2ToEC2SubnetRelProperties = (
        LoadBalancerV2ToEC2SubnetRelProperties()
    )


@dataclass(frozen=True)
class LoadBalancerV2Schema(CartographyNodeSchema):
    """
    LoadBalancerV2 schema (Application and Network Load Balancers).

    Target relationships (EXPOSE) are defined as MatchLinks below for introspection.
    """

    label: str = "LoadBalancerV2"
    properties: LoadBalancerV2NodeProperties = LoadBalancerV2NodeProperties()
    sub_resource_relationship: LoadBalancerV2ToAWSAccountRel = (
        LoadBalancerV2ToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            LoadBalancerV2ToEC2SecurityGroupRel(),
            LoadBalancerV2ToEC2SubnetRel(),
        ],
    )


# LoadBalancerV2 Target MatchLinks
# These define EXPOSE relationships to various target types


@dataclass(frozen=True)
class LoadBalancerV2ToTargetRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label",
        set_in_kwargs=True,
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)
    port: PropertyRef = PropertyRef("Port")
    protocol: PropertyRef = PropertyRef("Protocol")
    target_group_arn: PropertyRef = PropertyRef("TargetGroupArn")


@dataclass(frozen=True)
class LoadBalancerV2ToEC2InstanceMatchLink(CartographyRelSchema):
    """(:LoadBalancerV2)-[:EXPOSE]->(:EC2Instance)"""

    target_node_label: str = "EC2Instance"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"instanceid": PropertyRef("TargetId")},
    )
    source_node_label: str = "LoadBalancerV2"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("LoadBalancerId")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "EXPOSE"
    properties: LoadBalancerV2ToTargetRelProperties = (
        LoadBalancerV2ToTargetRelProperties()
    )


@dataclass(frozen=True)
class LoadBalancerV2ToEC2PrivateIpMatchLink(CartographyRelSchema):
    """(:LoadBalancerV2)-[:EXPOSE]->(:EC2PrivateIp)"""

    target_node_label: str = "EC2PrivateIp"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"private_ip_address": PropertyRef("TargetId")},
    )
    source_node_label: str = "LoadBalancerV2"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("LoadBalancerId")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "EXPOSE"
    properties: LoadBalancerV2ToTargetRelProperties = (
        LoadBalancerV2ToTargetRelProperties()
    )


@dataclass(frozen=True)
class LoadBalancerV2ToAWSLambdaMatchLink(CartographyRelSchema):
    """(:LoadBalancerV2)-[:EXPOSE]->(:AWSLambda)"""

    target_node_label: str = "AWSLambda"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TargetId")},
    )
    source_node_label: str = "LoadBalancerV2"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("LoadBalancerId")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "EXPOSE"
    properties: LoadBalancerV2ToTargetRelProperties = (
        LoadBalancerV2ToTargetRelProperties()
    )


@dataclass(frozen=True)
class LoadBalancerV2ToLoadBalancerV2MatchLink(CartographyRelSchema):
    """(:LoadBalancerV2)-[:EXPOSE]->(:LoadBalancerV2) for ALB targets"""

    target_node_label: str = "LoadBalancerV2"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("TargetId")},
    )
    source_node_label: str = "LoadBalancerV2"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("LoadBalancerId")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "EXPOSE"
    properties: LoadBalancerV2ToTargetRelProperties = (
        LoadBalancerV2ToTargetRelProperties()
    )


# ELBV2Listener Schema


@dataclass(frozen=True)
class ELBV2ListenerNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("ListenerArn")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    port: PropertyRef = PropertyRef("Port")
    protocol: PropertyRef = PropertyRef("Protocol")
    ssl_policy: PropertyRef = PropertyRef("SslPolicy")
    targetgrouparn: PropertyRef = PropertyRef("TargetGroupArn")


@dataclass(frozen=True)
class ELBV2ListenerToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ELBV2ListenerToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ELBV2ListenerToAWSAccountRelProperties = (
        ELBV2ListenerToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class ELBV2ListenerToLoadBalancerV2RelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ELBV2ListenerToLoadBalancerV2Rel(CartographyRelSchema):
    target_node_label: str = "LoadBalancerV2"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("LoadBalancerId")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "ELBV2_LISTENER"
    properties: ELBV2ListenerToLoadBalancerV2RelProperties = (
        ELBV2ListenerToLoadBalancerV2RelProperties()
    )


@dataclass(frozen=True)
class ELBV2ListenerSchema(CartographyNodeSchema):
    """
    ELBV2Listener schema for load balancer listeners.
    """

    label: str = "ELBV2Listener"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Endpoint"])
    properties: ELBV2ListenerNodeProperties = ELBV2ListenerNodeProperties()
    sub_resource_relationship: ELBV2ListenerToAWSAccountRel = (
        ELBV2ListenerToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [ELBV2ListenerToLoadBalancerV2Rel()],
    )
