from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
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
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )


@dataclass(frozen=True)
class APIGatewayV2APIToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AWSAPIGatewayV2API)<-[:RESOURCE]-(:AWSAccount)
class APIGatewayV2APIToAWSAccountRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSAPIGatewayV2API`."

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
    "Represents an `AWSAPIGatewayV2API` node in the AWS graph."

    label: str = "AWSAPIGatewayV2API"
    # DEPRECATED: legacy APIGatewayV2API node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["APIGatewayV2API"])
    properties: APIGatewayV2APINodeProperties = APIGatewayV2APINodeProperties()
    sub_resource_relationship: APIGatewayV2APIToAWSAccountRel = (
        APIGatewayV2APIToAWSAccountRel()
    )
