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
    id: PropertyRef = PropertyRef(
        "VpcPeeringConnectionId",
        description="vpcPeeringConnectionId, The ID of the VPC peering connection.",
    )
    allow_dns_resolution_from_remote_vpc: PropertyRef = PropertyRef(
        "AllowDnsResolutionFromRemoteVpc",
        description="Indicates whether a local VPC can resolve public DNS hostnames to private IP addresses when queried from instances in a peer VPC.",
    )
    allow_egress_from_local_classic_link_to_remote_vpc: PropertyRef = PropertyRef(
        "AllowEgressFromLocalClassicLinkToRemoteVpc",
        description="Indicates whether a local ClassicLink connection can communicate with the peer VPC over the VPC peering connection.",
    )
    allow_egress_from_local_vpc_to_remote_classic_link: PropertyRef = PropertyRef(
        "AllowEgressFromLocalVpcToRemoteClassicLink",
        description="Indicates whether a local VPC can communicate with a ClassicLink connection in the peer VPC over the VPC peering connection.",
    )
    requester_region: PropertyRef = PropertyRef(
        "RequesterRegion", description="Peering requester region"
    )
    accepter_region: PropertyRef = PropertyRef(
        "AccepterRegion", description="Peering accepter region"
    )
    status_code: PropertyRef = PropertyRef(
        "StatusCode", description="The status of the VPC peering connection."
    )
    status_message: PropertyRef = PropertyRef(
        "StatusMessage",
        description="A message that provides more information about the status, if applicable.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )


@dataclass(frozen=True)
class PeeringToAccepterVpcRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class PeeringToAccepterVpcRel(CartographyRelSchema):
    "Represents a `ACCEPTER_VPC` relationship from `AWSPeeringConnection` to `AWSVpc`."

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
    "Represents a `REQUESTER_VPC` relationship from `AWSPeeringConnection` to `AWSVpc`."

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
    "Represents a `ACCEPTER_CIDR` relationship from `AWSPeeringConnection` to `AWSCidrBlock`."

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
    "Represents a `REQUESTER_CIDR` relationship from `AWSPeeringConnection` to `AWSCidrBlock`."

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
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSPeeringConnection`."

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
    id: PropertyRef = PropertyRef("id", description="The AWS Account ID number")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )


@dataclass(frozen=True)
class AWSAccountVPCPeeringSchema(CartographyNodeSchema):
    "Represents an AWS account."

    # Implementation note:
    # Composite schema to represent AWS Accounts as known by VPC Peering.
    # Targets the same 'AWSAccount' label as the primary AWS account schema,
    # allowing MERGE operations to combine properties from both sources.

    label: str = "AWSAccount"  # Same label as primary AWSAccount schema
    properties: AWSAccountVPCPeeringNodeProperties = (
        AWSAccountVPCPeeringNodeProperties()
    )
    # No sub_resource_relationship - accounts are top-level entities


@dataclass(frozen=True)
class AWSPeeringConnectionSchema(CartographyNodeSchema):
    "Represents an `AWSPeeringConnection` node in the AWS graph."

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
