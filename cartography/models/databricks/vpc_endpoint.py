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
    id: PropertyRef = PropertyRef(
        "id",
        description="Account-scoped Databricks VPC endpoint ID.",
    )
    vpc_endpoint_id: PropertyRef = PropertyRef(
        "vpc_endpoint_id",
        extra_index=True,
        description="Databricks VPC endpoint ID.",
    )
    vpc_endpoint_name: PropertyRef = PropertyRef(
        "vpc_endpoint_name",
        extra_index=True,
        description="VPC endpoint name.",
    )
    aws_endpoint_service_id: PropertyRef = PropertyRef(
        "aws_endpoint_service_id",
        description="AWS endpoint service ID used by the VPC endpoint.",
    )
    region: PropertyRef = PropertyRef(
        "region",
        description="AWS region for the VPC endpoint.",
    )
    aws_vpc_endpoint_id: PropertyRef = PropertyRef(
        "aws_vpc_endpoint_id",
        extra_index=True,
        description="ID of the corresponding AWS VPC endpoint.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DatabricksVpcEndpointToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksAccount)-[:RESOURCE]->(:DatabricksVpcEndpoint)
class DatabricksVpcEndpointToAccountRel(CartographyRelSchema):
    """A Databricks account owns an account-level resource."""

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
    """A registered Databricks VPC endpoint points to an AWS VPC endpoint."""

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
    """A VPC endpoint registered with a Databricks account."""

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
