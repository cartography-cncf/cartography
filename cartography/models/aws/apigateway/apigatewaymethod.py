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
class APIGatewayMethodNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    httpmethod: PropertyRef = PropertyRef("httpMethod")
    resource_id: PropertyRef = PropertyRef("resourceId")
    api_id: PropertyRef = PropertyRef("apiId")
    authorization_type: PropertyRef = PropertyRef("authorizationType")
    authorizer_id: PropertyRef = PropertyRef("authorizerId")
    request_validator_id: PropertyRef = PropertyRef("requestValidatorId")
    operation_name: PropertyRef = PropertyRef("operationName")
    api_key_required: PropertyRef = PropertyRef("apiKeyRequired")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class APIGatewayMethodToAPIGatewayResourceRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class APIGatewayMethodToAPIGatewayResourceRel(CartographyRelSchema):
    target_node_label: str = "APIGatewayResource"
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
# (:APIGatewayMethod)<-[:RESOURCE]-(:AWSAccount)
class APIGatewayMethodToAWSAccountRel(CartographyRelSchema):
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
    label: str = "APIGatewayMethod"
    properties: APIGatewayMethodNodeProperties = APIGatewayMethodNodeProperties()
    sub_resource_relationship: APIGatewayMethodToAWSAccountRel = (
        APIGatewayMethodToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [APIGatewayMethodToAPIGatewayResourceRel()],
    )
