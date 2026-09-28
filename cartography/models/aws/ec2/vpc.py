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
from cartography.models.ontology.labels import VIRTUAL_NETWORK


@dataclass(frozen=True)
class VPCNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "VpcId", description="Unique identifier defined VPC node (vpcid)"
    )
    vpcid: PropertyRef = PropertyRef(
        "VpcId", extra_index=True, description="The VPC unique identifier"
    )
    primary_cidr_block: PropertyRef = PropertyRef(
        "PrimaryCIDRBlock", description="The primary IPv4 CIDR block for the VPC."
    )
    instance_tenancy: PropertyRef = PropertyRef(
        "InstanceTenancy",
        description="The allowed tenancy of instances launched into the VPC.",
    )
    state: PropertyRef = PropertyRef(
        "State", description="The current state of the VPC."
    )
    is_default: PropertyRef = PropertyRef(
        "IsDefault", description="Indicates whether the VPC is the default VPC."
    )
    dhcp_options_id: PropertyRef = PropertyRef(
        "DhcpOptionsId", description="The ID of a set of DHCP options."
    )
    region: PropertyRef = PropertyRef(
        "Region",
        set_in_kwargs=True,
        description="(optional) the region of this VPC.  This field is only available on VPCs in your account.  It is not available on VPCs that are external to your account and linked via a VPC peering relationship.",
    )
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
    """Representation of an [AWS VPC](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_Vpc.html). More information on https://docs.aws.amazon.com/cli/latest/reference/ec2/describe-vpcs.html"""

    label: str = "AWSVpc"
    properties: VPCNodeProperties = VPCNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([VIRTUAL_NETWORK])
    sub_resource_relationship: VPCToAWSAccountRel = VPCToAWSAccountRel()
