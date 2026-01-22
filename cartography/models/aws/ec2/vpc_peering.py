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
class VPCPeeringNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("VpcPeeringConnectionId")
    allow_dns_resolution_from_remote_vpc: PropertyRef = PropertyRef(
        "AllowDnsResolutionFromRemoteVpc",
    )
    allow_egress_from_local_classic_link_to_remote_vpc: PropertyRef = PropertyRef(
        "AllowEgressFromLocalClassicLinkToRemoteVpc",
    )
    allow_egress_from_local_vpc_to_remote_classic_link: PropertyRef = PropertyRef(
        "AllowEgressFromLocalVpcToRemoteClassicLink",
    )
    requester_region: PropertyRef = PropertyRef("RequesterRegion")
    accepter_region: PropertyRef = PropertyRef("AccepterRegion")
    status_code: PropertyRef = PropertyRef("StatusCode")
    status_message: PropertyRef = PropertyRef("StatusMessage")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class PeeringToAccepterVpcRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class PeeringToAccepterVpcRel(CartographyRelSchema):
    target_node_label: str = "AWSVpc"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AccepterVpcId")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ACCEPTER_VPC"
    properties: PeeringToAccepterVpcRelProperties = PeeringToAccepterVpcRelProperties()


@dataclass(frozen=True)
class PeeringToRequesterVpcRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class PeeringToRequesterVpcRel(CartographyRelSchema):
    target_node_label: str = "AWSVpc"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("RequesterVpcId")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "REQUESTER_VPC"
    properties: PeeringToRequesterVpcRelProperties = (
        PeeringToRequesterVpcRelProperties()
    )


@dataclass(frozen=True)
class PeeringToAccepterCidrRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class PeeringToAccepterCidrRel(CartographyRelSchema):
    target_node_label: str = "AWSCidrBlock"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCEPTER_CIDR_BLOCK_IDS", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ACCEPTER_CIDR"
    properties: PeeringToAccepterCidrRelProperties = (
        PeeringToAccepterCidrRelProperties()
    )


@dataclass(frozen=True)
class PeeringToRequesterCidrRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class PeeringToRequesterCidrRel(CartographyRelSchema):
    target_node_label: str = "AWSCidrBlock"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("REQUESTER_CIDR_BLOCK_IDS", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "REQUESTER_CIDR"
    properties: PeeringToRequesterCidrRelProperties = (
        PeeringToRequesterCidrRelProperties()
    )


@dataclass(frozen=True)
class PeeringConnectionToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class PeeringConnectionToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: PeeringConnectionToAWSAccountRelProperties = (
        PeeringConnectionToAWSAccountRelProperties()
    )


# Composite Node Pattern: AWSAccount as known by VPC Peering
@dataclass(frozen=True)
class AWSAccountVPCPeeringNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSAccountVPCPeeringSchema(CartographyNodeSchema):
    """
    Composite schema to represent AWS Accounts as known by VPC Peering.
    Targets the same 'AWSAccount' label as the primary AWS account schema,
    allowing MERGE operations to combine properties from both sources.
    """

    label: str = "AWSAccount"  # Same label as primary AWSAccount schema
    properties: AWSAccountVPCPeeringNodeProperties = (
        AWSAccountVPCPeeringNodeProperties()
    )
    # No sub_resource_relationship - accounts are top-level entities


@dataclass(frozen=True)
class AWSPeeringConnectionSchema(CartographyNodeSchema):
    label: str = "AWSPeeringConnection"
    properties: VPCPeeringNodeProperties = VPCPeeringNodeProperties()
    sub_resource_relationship: PeeringConnectionToAWSAccountRel = (
        PeeringConnectionToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            PeeringToAccepterVpcRel(),
            PeeringToRequesterVpcRel(),
            PeeringToAccepterCidrRel(),
            PeeringToRequesterCidrRel(),
        ],
    )
