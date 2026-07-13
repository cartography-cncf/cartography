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
class DatabricksVpcEndpointNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    vpc_endpoint_id: PropertyRef = PropertyRef("vpc_endpoint_id", extra_index=True)
    vpc_endpoint_name: PropertyRef = PropertyRef("vpc_endpoint_name", extra_index=True)
    aws_endpoint_service_id: PropertyRef = PropertyRef("aws_endpoint_service_id")
    region: PropertyRef = PropertyRef("region")
    aws_vpc_endpoint_id: PropertyRef = PropertyRef(
        "aws_vpc_endpoint_id", extra_index=True
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DatabricksVpcEndpointToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksAccount)-[:RESOURCE]->(:DatabricksVpcEndpoint)
class DatabricksVpcEndpointToAccountRel(CartographyRelSchema):
    target_node_label: str = "DatabricksAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DatabricksVpcEndpointToAccountRelProperties = (
        DatabricksVpcEndpointToAccountRelProperties()
    )


@dataclass(frozen=True)
class DatabricksVpcEndpointToAWSVpcEndpointRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksVpcEndpoint)-[:POINTS_TO]->(:AWSVpcEndpoint)
class DatabricksVpcEndpointToAWSVpcEndpointRel(CartographyRelSchema):
    target_node_label: str = "AWSVpcEndpoint"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("aws_vpc_endpoint_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "POINTS_TO"
    properties: DatabricksVpcEndpointToAWSVpcEndpointRelProperties = (
        DatabricksVpcEndpointToAWSVpcEndpointRelProperties()
    )


@dataclass(frozen=True)
class DatabricksVpcEndpointSchema(CartographyNodeSchema):
    label: str = "DatabricksVpcEndpoint"
    properties: DatabricksVpcEndpointNodeProperties = (
        DatabricksVpcEndpointNodeProperties()
    )
    sub_resource_relationship: DatabricksVpcEndpointToAccountRel = (
        DatabricksVpcEndpointToAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [DatabricksVpcEndpointToAWSVpcEndpointRel()],
    )
