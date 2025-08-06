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
class VPCNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("VpcId")
    vpcid: PropertyRef = PropertyRef("VpcId", extra_index=True)
    primary_cidr_block: PropertyRef = PropertyRef("PrimaryCIDRBlock")
    instance_tenancy: PropertyRef = PropertyRef("InstanceTenancy")
    state: PropertyRef = PropertyRef("State")
    is_default: PropertyRef = PropertyRef("IsDefault")
    dhcp_options_id: PropertyRef = PropertyRef("DhcpOptionsId")
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class VPCToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class VPCToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: VPCToAWSAccountRelProperties = VPCToAWSAccountRelProperties()


@dataclass(frozen=True)
class AWSVpcSchema(CartographyNodeSchema):
    label: str = "AWSVpc"
    properties: VPCNodeProperties = VPCNodeProperties()
    sub_resource_relationship: VPCToAWSAccountRel = VPCToAWSAccountRel()
