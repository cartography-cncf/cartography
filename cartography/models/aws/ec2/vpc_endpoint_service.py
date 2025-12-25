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
class AWSEc2VpcEndpointServiceNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("ServiceId")
    service_id: PropertyRef = PropertyRef("ServiceId")
    service_name: PropertyRef = PropertyRef("ServiceName")
    service_state: PropertyRef = PropertyRef("ServiceState")
    acceptance_required: PropertyRef = PropertyRef("AcceptanceRequired")
    manages_vpc_endpoints: PropertyRef = PropertyRef("ManagesVpcEndpoints")
    private_dns_name: PropertyRef = PropertyRef("PrivateDnsName")
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSEc2VpcEndpointServiceToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSEc2VpcEndpointServiceToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AWSEc2VpcEndpointServiceToAWSAccountRelProperties = (
        AWSEc2VpcEndpointServiceToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class AWSEc2VpcEndpointServiceSchema(CartographyNodeSchema):
    label: str = "AWSEc2VpcEndpointService"
    properties: AWSEc2VpcEndpointServiceNodeProperties = (
        AWSEc2VpcEndpointServiceNodeProperties()
    )
    sub_resource_relationship: AWSEc2VpcEndpointServiceToAWSAccountRel = (
        AWSEc2VpcEndpointServiceToAWSAccountRel()
    )
