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
class ElasticIPAddressNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("PublicIp")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    public_ip: PropertyRef = PropertyRef("PublicIp", extra_index=True)
    instance_id: PropertyRef = PropertyRef("InstanceId")
    allocation_id: PropertyRef = PropertyRef("AllocationId")
    association_id: PropertyRef = PropertyRef("AssociationId")
    domain: PropertyRef = PropertyRef("Domain")
    network_interface_id: PropertyRef = PropertyRef("NetworkInterfaceId")
    network_interface_owner_id: PropertyRef = PropertyRef("NetworkInterfaceOwnerId")
    private_ip_address: PropertyRef = PropertyRef("PrivateIpAddress")
    public_ipv4_pool: PropertyRef = PropertyRef("PublicIpv4Pool")
    network_border_group: PropertyRef = PropertyRef("NetworkBorderGroup")
    customer_owned_ip: PropertyRef = PropertyRef("CustomerOwnedIp")
    customer_owned_ipv4_pool: PropertyRef = PropertyRef("CustomerOwnedIpv4Pool")
    carrier_ip: PropertyRef = PropertyRef("CarrierIp")


@dataclass(frozen=True)
class ElasticIPAddressToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ElasticIPAddressToAWSAccountRel(CartographyRelSchema):
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
    target_node_label: str = "EC2Instance"
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
    target_node_label: str = "NetworkInterface"
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
    label: str = "ElasticIPAddress"
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
