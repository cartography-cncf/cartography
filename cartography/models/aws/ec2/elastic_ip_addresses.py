from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class ElasticIPAddressNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("PublicIp", description="The Elastic IP address")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )
    region: PropertyRef = PropertyRef(
        "Region", set_in_kwargs=True, description="The region of the IP."
    )
    public_ip: PropertyRef = PropertyRef(
        "PublicIp", extra_index=True, description="The Elastic IP address."
    )
    instance_id: PropertyRef = PropertyRef(
        "InstanceId",
        description="The ID of the instance that the address is associated with (if any).",
    )
    allocation_id: PropertyRef = PropertyRef(
        "AllocationId",
        description="The ID representing the allocation of the address for use with EC2-VPC.",
    )
    association_id: PropertyRef = PropertyRef(
        "AssociationId",
        description="The ID representing the association of the address with an instance in a VPC.",
    )
    domain: PropertyRef = PropertyRef(
        "Domain",
        description="Indicates whether this Elastic IP address is for use with instances in EC2-Classic (standard) or instances in a VPC (vpc).",
    )
    network_interface_id: PropertyRef = PropertyRef(
        "NetworkInterfaceId", description="The ID of the network interface."
    )
    network_interface_owner_id: PropertyRef = PropertyRef(
        "NetworkInterfaceOwnerId",
        description="Identifier of the network interface owner linked to this `AWSElasticIPAddress` node.",
    )
    private_ip_address: PropertyRef = PropertyRef(
        "PrivateIpAddress",
        description="The private IP address associated with the Elastic IP address.",
    )
    public_ipv4_pool: PropertyRef = PropertyRef(
        "PublicIpv4Pool", description="The ID of an address pool."
    )
    network_border_group: PropertyRef = PropertyRef(
        "NetworkBorderGroup",
        description="The name of the unique set of Availability Zones, Local Zones, or Wavelength Zones from which AWS advertises IP addresses.",
    )
    customer_owned_ip: PropertyRef = PropertyRef(
        "CustomerOwnedIp", description="The customer-owned IP address."
    )
    customer_owned_ipv4_pool: PropertyRef = PropertyRef(
        "CustomerOwnedIpv4Pool",
        description="The ID of the customer-owned address pool.",
    )
    carrier_ip: PropertyRef = PropertyRef(
        "CarrierIp",
        description="The carrier IP address associated. This option is only available for network interfaces which reside in a subnet in a Wavelength Zone (for example an EC2 instance).",
    )


@dataclass(frozen=True)
class ElasticIPAddressToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ElasticIPAddressToAWSAccountRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSElasticIPAddress`."

    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ElasticIPAddressToAWSAccountRelProperties = (
        ElasticIPAddressToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class ElasticIPAddressToEC2InstanceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ElasticIPAddressToEC2InstanceRel(CartographyRelSchema):
    "Represents a `ELASTIC_IP_ADDRESS` relationship from `AWSEC2Instance` to `AWSElasticIPAddress`."

    target_node_label: str = "AWSEC2Instance"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("InstanceId")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "ELASTIC_IP_ADDRESS"
    properties: ElasticIPAddressToEC2InstanceRelProperties = (
        ElasticIPAddressToEC2InstanceRelProperties()
    )


@dataclass(frozen=True)
class ElasticIPAddressToNetworkInterfaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ElasticIPAddressToNetworkInterfaceRel(CartographyRelSchema):
    "Represents a `ELASTIC_IP_ADDRESS` relationship from `AWSNetworkInterface` to `AWSElasticIPAddress`."

    target_node_label: str = "AWSNetworkInterface"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("NetworkInterfaceId")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "ELASTIC_IP_ADDRESS"
    properties: ElasticIPAddressToNetworkInterfaceRelProperties = (
        ElasticIPAddressToNetworkInterfaceRelProperties()
    )


@dataclass(frozen=True)
class ElasticIPAddressSchema(CartographyNodeSchema):
    "Represents an `AWSElasticIPAddress` node in the AWS graph."

    label: str = "AWSElasticIPAddress"
    # DEPRECATED: legacy ElasticIPAddress node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["ElasticIPAddress"])
    properties: ElasticIPAddressNodeProperties = ElasticIPAddressNodeProperties()
    sub_resource_relationship: ElasticIPAddressToAWSAccountRel = (
        ElasticIPAddressToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            ElasticIPAddressToEC2InstanceRel(),
            ElasticIPAddressToNetworkInterfaceRel(),
        ],
    )
