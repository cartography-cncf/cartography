from dataclasses import dataclass

from cartography.models.aws.extra_labels import LEGACY_API_GATEWAY_V2_API
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
class APIGatewayV2APINodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", extra_index=True, description="The id of the API"
    )
    name: PropertyRef = PropertyRef("name", description="The name of the API")
    protocoltype: PropertyRef = PropertyRef(
        "protocolType", description="The protocol type (HTTP or WEBSOCKET)"
    )
    routeselectionexpression: PropertyRef = PropertyRef(
        "routeSelectionExpression", description="Expression for selecting routes"
    )
    apikeyselectionexpression: PropertyRef = PropertyRef(
        "apiKeySelectionExpression", description="Expression for selecting API keys"
    )
    apiendpoint: PropertyRef = PropertyRef(
        "apiEndpoint", description="The endpoint URL of the API"
    )
    version: PropertyRef = PropertyRef(
        "version", description="The version identifier for the API"
    )
    createddate: PropertyRef = PropertyRef(
        "createdDate", description="The timestamp when the API was created"
    )
    description: PropertyRef = PropertyRef(
        "description", description="The description of the API"
    )
    region: PropertyRef = PropertyRef(
        "region", set_in_kwargs=True, description="The region where the API is created"
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class APIGatewayV2APIToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AWSAPIGatewayV2API)<-[:RESOURCE]-(:AWSAccount)
class APIGatewayV2APIToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: APIGatewayV2APIToAWSAccountRelProperties = (
        APIGatewayV2APIToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class APIGatewayV2APISchema(CartographyNodeSchema):
    """Representation of an AWS [API Gateway v2 API](https://docs.aws.amazon.com/apigatewayv2/latest/api-reference/apis.html#apisget)."""

    label: str = "AWSAPIGatewayV2API"
    # DEPRECATED: legacy APIGatewayV2API node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([LEGACY_API_GATEWAY_V2_API])
    properties: APIGatewayV2APINodeProperties = APIGatewayV2APINodeProperties()
    sub_resource_relationship: APIGatewayV2APIToAWSAccountRel = (
        APIGatewayV2APIToAWSAccountRel()
    )


@dataclass(frozen=True)
class APIGatewayV2StageNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "arn", extra_index=True, description="The ARN of the API Gateway v2 stage"
    )
    stagename: PropertyRef = PropertyRef(
        "stageName", description="The name of the API Gateway v2 stage"
    )
    autodeploy: PropertyRef = PropertyRef(
        "autoDeploy",
        description="Whether the stage deploys the latest API configuration automatically",
    )
    deploymentid: PropertyRef = PropertyRef(
        "deploymentId",
        description="The identifier of the Deployment that the stage points to",
    )
    description: PropertyRef = PropertyRef(
        "description", description="The description of the stage"
    )
    createddate: PropertyRef = PropertyRef(
        "createdDate", description="The timestamp when the stage was created"
    )
    lastupdateddate: PropertyRef = PropertyRef(
        "lastUpdatedDate", description="The timestamp when the stage was last updated"
    )
    apigatewaymanaged: PropertyRef = PropertyRef(
        "apiGatewayManaged",
        description="Whether the stage is managed by API Gateway",
    )
    clientcertificateid: PropertyRef = PropertyRef(
        "clientCertificateId",
        description="The identifier of a client certificate for the stage",
    )
    region: PropertyRef = PropertyRef(
        "region",
        set_in_kwargs=True,
        description="The region where the stage is created",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class APIGatewayV2StageToAWSAPIGatewayV2APIRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AWSAPIGatewayV2Stage)<-[:ASSOCIATED_WITH]-(:AWSAPIGatewayV2API)
class APIGatewayV2StageToAWSAPIGatewayV2APIRel(CartographyRelSchema):
    target_node_label: str = "AWSAPIGatewayV2API"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("apiId")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "ASSOCIATED_WITH"
    properties: APIGatewayV2StageToAWSAPIGatewayV2APIRelProperties = (
        APIGatewayV2StageToAWSAPIGatewayV2APIRelProperties()
    )


@dataclass(frozen=True)
class APIGatewayV2StageToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AWSAPIGatewayV2Stage)<-[:RESOURCE]-(:AWSAccount)
class APIGatewayV2StageToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: APIGatewayV2StageToAWSAccountRelProperties = (
        APIGatewayV2StageToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class APIGatewayV2StageSchema(CartographyNodeSchema):
    """
    Representation of an AWS [API Gateway v2 Stage](https://docs.aws.amazon.com/apigatewayv2/latest/api-reference/apis-apiid-stages.html).
    """

    label: str = "AWSAPIGatewayV2Stage"
    properties: APIGatewayV2StageNodeProperties = APIGatewayV2StageNodeProperties()
    sub_resource_relationship: APIGatewayV2StageToAWSAccountRel = (
        APIGatewayV2StageToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [APIGatewayV2StageToAWSAPIGatewayV2APIRel()],
    )
