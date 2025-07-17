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


@dataclass(frozen=True)
class LoadBalancerV2NodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("DNSName")
    name: PropertyRef = PropertyRef("LoadBalancerName")
    dnsname: PropertyRef = PropertyRef("DNSName", extra_index=True)
    canonicalhostedzonenameid: PropertyRef = PropertyRef("CanonicalHostedZoneNameID")
    type: PropertyRef = PropertyRef("Type")
    scheme: PropertyRef = PropertyRef("Scheme")
    createdtime: PropertyRef = PropertyRef("CreatedTime")
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class LoadBalancerV2ToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class LoadBalancerV2ToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("AWS_ID", set_in_kwargs=True),
        }
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
        {
            "groupid": PropertyRef("SecurityGroups", one_to_many=True),
        }
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
        {
            "subnetid": PropertyRef("SubnetIds", one_to_many=True),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "SUBNET"
    properties: LoadBalancerV2ToEC2SubnetRelProperties = (
        LoadBalancerV2ToEC2SubnetRelProperties()
    )


@dataclass(frozen=True)
class LoadBalancerV2Schema(CartographyNodeSchema):
    label: str = "LoadBalancerV2"
    properties: LoadBalancerV2NodeProperties = LoadBalancerV2NodeProperties()
    sub_resource_relationship: LoadBalancerV2ToAWSAccountRel = (
        LoadBalancerV2ToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            LoadBalancerV2ToEC2SecurityGroupRel(),
            LoadBalancerV2ToEC2SubnetRel(),
        ]
    )


@dataclass(frozen=True)
class ELBV2ListenerNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("ListenerArn")
    port: PropertyRef = PropertyRef("Port")
    protocol: PropertyRef = PropertyRef("Protocol")
    ssl_policy: PropertyRef = PropertyRef("SslPolicy")
    targetgrouparn: PropertyRef = PropertyRef("TargetGroupArn")
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ELBV2ListenerToLoadBalancerV2RelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ELBV2ListenerToLoadBalancerV2Rel(CartographyRelSchema):
    target_node_label: str = "LoadBalancerV2"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("LoadBalancerId"),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "ELBV2_LISTENER"
    properties: ELBV2ListenerToLoadBalancerV2RelProperties = (
        ELBV2ListenerToLoadBalancerV2RelProperties()
    )


@dataclass(frozen=True)
class ELBV2ListenerToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ELBV2ListenerToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("AWS_ID", set_in_kwargs=True),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ELBV2ListenerToAWSAccountRelProperties = (
        ELBV2ListenerToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class ELBV2ListenerSchema(CartographyNodeSchema):
    label: str = "ELBV2Listener"
    properties: ELBV2ListenerNodeProperties = ELBV2ListenerNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Endpoint"])
    sub_resource_relationship: ELBV2ListenerToAWSAccountRel = (
        ELBV2ListenerToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            ELBV2ListenerToLoadBalancerV2Rel(),
        ]
    )


@dataclass(frozen=True)
class LoadBalancerV2ExposeInstanceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label", set_in_kwargs=True
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)
    port: PropertyRef = PropertyRef("Port")
    protocol: PropertyRef = PropertyRef("Protocol")
    target_group_arn: PropertyRef = PropertyRef("TargetGroupArn")


@dataclass(frozen=True)
class LoadBalancerV2ExposeInstanceMatchLink(CartographyRelSchema):
    target_node_label: str = "EC2Instance"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "instanceid": PropertyRef("InstanceId"),
        }
    )
    source_node_label: str = "LoadBalancerV2"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {
            "id": PropertyRef("ElbV2Id"),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "EXPOSE"
    properties: LoadBalancerV2ExposeInstanceRelProperties = (
        LoadBalancerV2ExposeInstanceRelProperties()
    )
