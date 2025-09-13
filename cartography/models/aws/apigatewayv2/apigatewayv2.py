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
class APIGatewayV2APINodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", extra_index=True)
    name: PropertyRef = PropertyRef("name")
    protocoltype: PropertyRef = PropertyRef("protocolType")
    routeselectionexpression: PropertyRef = PropertyRef("routeSelectionExpression")
    apikeyselectionexpression: PropertyRef = PropertyRef("apiKeySelectionExpression")
    apiendpoint: PropertyRef = PropertyRef("apiEndpoint")
    version: PropertyRef = PropertyRef("version")
    createddate: PropertyRef = PropertyRef("createdDate")
    description: PropertyRef = PropertyRef("description")
    region: PropertyRef = PropertyRef("region", set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class APIGatewayV2APIToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:APIGatewayV2API)<-[:RESOURCE]-(:AWSAccount)
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
    label: str = "APIGatewayV2API"
    properties: APIGatewayV2APINodeProperties = APIGatewayV2APINodeProperties()
    sub_resource_relationship: APIGatewayV2APIToAWSAccountRel = (
        APIGatewayV2APIToAWSAccountRel()
    )
