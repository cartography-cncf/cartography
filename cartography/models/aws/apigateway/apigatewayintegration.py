from dataclasses import dataclass

from cartography.models.aws.extra_labels import LEGACY_API_GATEWAY_INTEGRATION
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
class APIGatewayIntegrationNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="The id represented as ApiId/ResourceId/HttpMethod"
    )
    httpmethod: PropertyRef = PropertyRef(
        "httpMethod", description="Specifies a get integration request's HTTP method"
    )
    integration_http_method: PropertyRef = PropertyRef(
        "integrationHttpMethod",
        description="Specifies the integration's HTTP method type",
    )
    resource_id: PropertyRef = PropertyRef(
        "resourceId", description="Identifier for respective resource"
    )
    api_id: PropertyRef = PropertyRef(
        "apiId", description="The  identifier for the API"
    )
    type: PropertyRef = PropertyRef(
        "type", description="Specifies an API method integration type"
    )
    uri: PropertyRef = PropertyRef(
        "uri",
        description="Specifies Uniform Resource Identifier (URI) of the integration endpoint",
    )
    connection_type: PropertyRef = PropertyRef(
        "connectionType",
        description="The type of the network connection to the integration endpoint",
    )
    connection_id: PropertyRef = PropertyRef(
        "connectionId",
        description="The ID of the VpcLink used for the integration when connectionType=VPC_LINK and undefined, otherwise",
    )
    credentials: PropertyRef = PropertyRef(
        "credentials",
        description="Specifies the credentials required for the integration, if any",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class APIGatewayIntegrationToAPIGatewayResourceRelRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class APIGatewayIntegrationToAPIGatewayResourceRel(CartographyRelSchema):
    target_node_label: str = "AWSAPIGatewayResource"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("resourceId")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_INTEGRATION"
    properties: APIGatewayIntegrationToAPIGatewayResourceRelRelProperties = (
        APIGatewayIntegrationToAPIGatewayResourceRelRelProperties()
    )


@dataclass(frozen=True)
class APIGatewayIntegrationToAWSAccountRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AWSAPIGatewayIntegration)<-[:RESOURCE]-(:AWSAccount)
class APIGatewayIntegrationToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: APIGatewayIntegrationToAWSAccountRelRelProperties = (
        APIGatewayIntegrationToAWSAccountRelRelProperties()
    )


@dataclass(frozen=True)
class APIGatewayIntegrationSchema(CartographyNodeSchema):
    """Representation of an AWS [API Gateway Integration](https://docs.aws.amazon.com/apigateway/latest/api/API_GetIntegration.html)."""

    label: str = "AWSAPIGatewayIntegration"
    # DEPRECATED: legacy APIGatewayIntegration node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        [LEGACY_API_GATEWAY_INTEGRATION]
    )
    properties: APIGatewayIntegrationNodeProperties = (
        APIGatewayIntegrationNodeProperties()
    )
    sub_resource_relationship: APIGatewayIntegrationToAWSAccountRel = (
        APIGatewayIntegrationToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [APIGatewayIntegrationToAPIGatewayResourceRel()],
    )
