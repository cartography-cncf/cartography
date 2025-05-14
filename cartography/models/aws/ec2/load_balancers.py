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
class LoadBalancerNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name")
    dnsname: PropertyRef = PropertyRef("dnsname", extra_index=True)
    canonicalhostedzonename: PropertyRef = PropertyRef("canonicalhostedzonename")
    canonicalhostedzonenameid: PropertyRef = PropertyRef("canonicalhostedzonenameid")
    scheme: PropertyRef = PropertyRef("scheme")
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    createdtime: PropertyRef = PropertyRef("createdtime")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class LoadBalancerToAWSAccountRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class LoadBalancerToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: LoadBalancerToAWSAccountRelRelProperties = (
        LoadBalancerToAWSAccountRelRelProperties()
    )


@dataclass(frozen=True)
class LoadBalancerToSecurityGroupRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class LoadBalancerToSourceSecurityGroupRel(CartographyRelSchema):
    target_node_label: str = "EC2SecurityGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"name": PropertyRef("GROUP_NAME")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "SOURCE_SECURITY_GROUP"
    properties: LoadBalancerToSecurityGroupRelProperties = (
        LoadBalancerToSecurityGroupRelProperties()
    )


@dataclass(frozen=True)
class LoadBalancerToEC2SecurityGroupRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class LoadBalancerToEC2SecurityGroupRel(CartographyRelSchema):
    target_node_label: str = "EC2SecurityGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"groupid": PropertyRef("GROUP_IDS", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MEMBER_OF_EC2_SECURITY_GROUP"
    properties: LoadBalancerToEC2SecurityGroupRelRelProperties = (
        LoadBalancerToEC2SecurityGroupRelRelProperties()
    )


@dataclass(frozen=True)
class LoadBalancerToEC2InstanceRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class LoadBalancerToEC2InstanceRel(CartographyRelSchema):
    target_node_label: str = "EC2Instance"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"instanceid": PropertyRef("INSTANCE_IDS", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "EXPOSE"
    properties: LoadBalancerToEC2InstanceRelRelProperties = (
        LoadBalancerToEC2InstanceRelRelProperties()
    )


@dataclass(frozen=True)
class LoadBalancerSchema(CartographyNodeSchema):
    label: str = "LoadBalancer"
    properties: LoadBalancerNodeProperties = LoadBalancerNodeProperties()
    sub_resource_relationship: LoadBalancerToAWSAccountRel = (
        LoadBalancerToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            LoadBalancerToSourceSecurityGroupRel(),
            LoadBalancerToEC2SecurityGroupRel(),
            LoadBalancerToEC2InstanceRel(),
        ],
    )
