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
    id: PropertyRef = PropertyRef("VpcEndpointId")
    vpc_endpoint_id: PropertyRef = PropertyRef("VpcEndpointId", extra_index=True)
    vpc_id: PropertyRef = PropertyRef("VpcId")
    service_name: PropertyRef = PropertyRef("ServiceName")
    service_region: PropertyRef = PropertyRef("ServiceRegion")
    vpc_endpoint_type: PropertyRef = PropertyRef("VpcEndpointType")
    state: PropertyRef = PropertyRef("State")
    policy_document: PropertyRef = PropertyRef("PolicyDocument")
    route_table_ids: PropertyRef = PropertyRef("RouteTableIds")
    subnet_ids: PropertyRef = PropertyRef("SubnetIds")
    network_interface_ids: PropertyRef = PropertyRef("NetworkInterfaceIds")
    dns_entries: PropertyRef = PropertyRef("DnsEntries")
    private_dns_enabled: PropertyRef = PropertyRef("PrivateDnsEnabled")
    requester_managed: PropertyRef = PropertyRef("RequesterManaged")
    ip_address_type: PropertyRef = PropertyRef("IpAddressType")
    owner_id: PropertyRef = PropertyRef("OwnerId")
    creation_timestamp: PropertyRef = PropertyRef("CreationTimestamp")
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class VPCEndpointToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class VPCEndpointToAWSAccountRel(CartographyRelSchema):
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
    target_node_label: str = "AWSVpc"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("VpcId")}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MEMBER_OF_AWS_VPC"
    properties: VPCEndpointToVPCRelProperties = VPCEndpointToVPCRelProperties()


@dataclass(frozen=True)
class AWSVpcEndpointSchema(CartographyNodeSchema):
    label: str = "AWSVpcEndpoint"
    properties: VPCEndpointNodeProperties = VPCEndpointNodeProperties()
    sub_resource_relationship: VPCEndpointToAWSAccountRel = VPCEndpointToAWSAccountRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            VPCEndpointToVPCRel(),
        ]
    )
