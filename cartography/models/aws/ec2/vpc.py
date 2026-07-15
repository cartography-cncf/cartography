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
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )


@dataclass(frozen=True)
class VPCToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class VPCToAWSAccountRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSVpc`."

    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: VPCToAWSAccountRelProperties = VPCToAWSAccountRelProperties()


@dataclass(frozen=True)
class AWSVpcSchema(CartographyNodeSchema):
    "Represents an `AWSVpc` node in the AWS graph."

    label: str = "AWSVpc"
    properties: VPCNodeProperties = VPCNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["VirtualNetwork"])
    sub_resource_relationship: VPCToAWSAccountRel = VPCToAWSAccountRel()
