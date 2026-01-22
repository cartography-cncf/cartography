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
class APIGatewayIntegrationNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    httpmethod: PropertyRef = PropertyRef("httpMethod")
    integration_http_method: PropertyRef = PropertyRef("integrationHttpMethod")
    resource_id: PropertyRef = PropertyRef("resourceId")
    api_id: PropertyRef = PropertyRef("apiId")
    type: PropertyRef = PropertyRef("type")
    uri: PropertyRef = PropertyRef("uri")
    connection_type: PropertyRef = PropertyRef("connectionType")
    connection_id: PropertyRef = PropertyRef("connectionId")
    credentials: PropertyRef = PropertyRef("credentials")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class APIGatewayIntegrationToAPIGatewayResourceRelRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class APIGatewayIntegrationToAPIGatewayResourceRel(CartographyRelSchema):
    target_node_label: str = "APIGatewayResource"
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
# (:APIGatewayIntegration)<-[:RESOURCE]-(:AWSAccount)
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
    label: str = "APIGatewayIntegration"
    properties: APIGatewayIntegrationNodeProperties = (
        APIGatewayIntegrationNodeProperties()
    )
    sub_resource_relationship: APIGatewayIntegrationToAWSAccountRel = (
        APIGatewayIntegrationToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [APIGatewayIntegrationToAPIGatewayResourceRel()],
    )
