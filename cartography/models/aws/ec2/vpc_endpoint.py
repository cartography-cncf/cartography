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
class VPCEndpointNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "VpcEndpointId", description="Unique identifier for this `AWSVpcEndpoint` node."
    )
    vpc_endpoint_id: PropertyRef = PropertyRef(
        "VpcEndpointId",
        extra_index=True,
        description="Identifier of the VPC endpoint linked to this `AWSVpcEndpoint` node.",
    )
    vpc_id: PropertyRef = PropertyRef(
        "VpcId",
        description="Identifier of the VPC linked to this `AWSVpcEndpoint` node.",
    )
    service_name: PropertyRef = PropertyRef(
        "ServiceName",
        description="AWS service name exposed through the VPC endpoint.",
    )
    service_region: PropertyRef = PropertyRef(
        "ServiceRegion",
        description="AWS Region in which the endpoint service is available.",
    )
    vpc_endpoint_type: PropertyRef = PropertyRef(
        "VpcEndpointType",
        description="VPC endpoint type, such as Interface, Gateway, or GatewayLoadBalancer.",
    )
    state: PropertyRef = PropertyRef(
        "State", description="Current lifecycle state of this `AWSVpcEndpoint` node."
    )
    policy_document: PropertyRef = PropertyRef(
        "PolicyDocument",
        description="JSON access policy attached to the VPC endpoint.",
    )
    route_table_ids: PropertyRef = PropertyRef(
        "RouteTableIds",
        description="Identifiers of the route table linked to this `AWSVpcEndpoint` node.",
    )
    subnet_ids: PropertyRef = PropertyRef(
        "SubnetIds",
        description="Identifiers of the subnet linked to this `AWSVpcEndpoint` node.",
    )
    network_interface_ids: PropertyRef = PropertyRef(
        "NetworkInterfaceIds",
        description="Identifiers of the network interface linked to this `AWSVpcEndpoint` node.",
    )
    dns_entries: PropertyRef = PropertyRef(
        "DnsEntries",
        description="DNS names and hosted-zone identifiers assigned to the VPC endpoint.",
    )
    private_dns_enabled: PropertyRef = PropertyRef(
        "PrivateDnsEnabled",
        description="Whether private dns is enabled for this `AWSVpcEndpoint` node.",
    )
    requester_managed: PropertyRef = PropertyRef(
        "RequesterManaged",
        description="Whether this `AWSVpcEndpoint` node is managed by its service requester.",
    )
    ip_address_type: PropertyRef = PropertyRef(
        "IpAddressType",
        description="IP address family supported by the VPC endpoint.",
    )
    owner_id: PropertyRef = PropertyRef(
        "OwnerId",
        description="Identifier of the owner linked to this `AWSVpcEndpoint` node.",
    )
    creation_timestamp: PropertyRef = PropertyRef(
        "CreationTimestamp",
        description="Timestamp when the VPC endpoint was created.",
    )
    region: PropertyRef = PropertyRef(
        "Region",
        set_in_kwargs=True,
        description="AWS Region containing this `AWSVpcEndpoint` node.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that updated this `AWSVpcEndpoint` node.",
    )


@dataclass(frozen=True)
class VPCEndpointToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class VPCEndpointToAWSAccountRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSVpcEndpoint`."

    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: VPCEndpointToAWSAccountRelProperties = (
        VPCEndpointToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class VPCEndpointToVPCRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class VPCEndpointToVPCRel(CartographyRelSchema):
    "Represents a `MEMBER_OF_AWS_VPC` relationship from `AWSVpcEndpoint` to `AWSVpc`."

    target_node_label: str = "AWSVpc"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("VpcId")}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MEMBER_OF_AWS_VPC"
    properties: VPCEndpointToVPCRelProperties = VPCEndpointToVPCRelProperties()


@dataclass(frozen=True)
class AWSVpcEndpointSchema(CartographyNodeSchema):
    "Represents an `AWSVpcEndpoint` node in the AWS graph."

    label: str = "AWSVpcEndpoint"
    properties: VPCEndpointNodeProperties = VPCEndpointNodeProperties()
    sub_resource_relationship: VPCEndpointToAWSAccountRel = VPCEndpointToAWSAccountRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            VPCEndpointToVPCRel(),
        ]
    )
