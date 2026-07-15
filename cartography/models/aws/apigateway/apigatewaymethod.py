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
class APIGatewayMethodNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="The id represented as ApiId/ResourceId/HttpMethod"
    )
    httpmethod: PropertyRef = PropertyRef(
        "httpMethod", description="The method's HTTP verb"
    )
    resource_id: PropertyRef = PropertyRef(
        "resourceId", description="Identifier for respective resource"
    )
    api_id: PropertyRef = PropertyRef(
        "apiId", description="The  identifier for the API"
    )
    authorization_type: PropertyRef = PropertyRef(
        "authorizationType", description="The method's authorization type"
    )
    authorizer_id: PropertyRef = PropertyRef(
        "authorizerId",
        description="The identifier of an authorizer to use on this method",
    )
    request_validator_id: PropertyRef = PropertyRef(
        "requestValidatorId",
        description="The identifier of a RequestValidator for request validation",
    )
    operation_name: PropertyRef = PropertyRef(
        "operationName",
        description="A human-friendly operation identifier for the method",
    )
    api_key_required: PropertyRef = PropertyRef(
        "apiKeyRequired",
        description="A boolean flag specifying whether a valid ApiKey is required to invoke this method",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )


@dataclass(frozen=True)
class APIGatewayMethodToAPIGatewayResourceRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class APIGatewayMethodToAPIGatewayResourceRel(CartographyRelSchema):
    "Represents a `HAS_METHOD` relationship from `AWSAPIGatewayResource` to `AWSAPIGatewayMethod`."

    target_node_label: str = "AWSAPIGatewayResource"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("resourceId")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_METHOD"
    properties: APIGatewayMethodToAPIGatewayResourceRelRelProperties = (
        APIGatewayMethodToAPIGatewayResourceRelRelProperties()
    )


@dataclass(frozen=True)
class APIGatewayMethodToAWSAccountRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AWSAPIGatewayMethod)<-[:RESOURCE]-(:AWSAccount)
class APIGatewayMethodToAWSAccountRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSAPIGatewayMethod`."

    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: APIGatewayMethodToAWSAccountRelRelProperties = (
        APIGatewayMethodToAWSAccountRelRelProperties()
    )


@dataclass(frozen=True)
class APIGatewayMethodSchema(CartographyNodeSchema):
    "Represents an `AWSAPIGatewayMethod` node in the AWS graph."

    label: str = "AWSAPIGatewayMethod"
    # DEPRECATED: legacy APIGatewayMethod node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["APIGatewayMethod"])
    properties: APIGatewayMethodNodeProperties = APIGatewayMethodNodeProperties()
    sub_resource_relationship: APIGatewayMethodToAWSAccountRel = (
        APIGatewayMethodToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [APIGatewayMethodToAPIGatewayResourceRel()],
    )
