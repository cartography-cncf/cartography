from dataclasses import dataclass

from cartography.models.aws.extra_labels import LEGACY_API_GATEWAY_RESOURCE
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
class APIGatewayResourceNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="The id of the resource")
    path: PropertyRef = PropertyRef("path", description="The full path of the resource")
    pathpart: PropertyRef = PropertyRef(
        "pathPart", description="The last path segment of the resource"
    )
    parentid: PropertyRef = PropertyRef(
        "parentId",
        description="The id of the parent resource",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class APIGatewayResourceToRestAPIRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AWSAPIGatewayResource)<-[:RESOURCE]-(:AWSAPIGatewayRestAPI)
class APIGatewayResourceToRestAPIRel(CartographyRelSchema):
    target_node_label: str = "AWSAPIGatewayRestAPI"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("apiId")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: APIGatewayResourceToRestAPIRelRelProperties = (
        APIGatewayResourceToRestAPIRelRelProperties()
    )


@dataclass(frozen=True)
class APIGatewayResourceToAWSAccountRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AWSAPIGatewayResource)<-[:RESOURCE]-(:AWSAccount)
class APIGatewayResourceToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: APIGatewayResourceToAWSAccountRelRelProperties = (
        APIGatewayResourceToAWSAccountRelRelProperties()
    )


@dataclass(frozen=True)
class APIGatewayResourceSchema(CartographyNodeSchema):
    """Representation of an AWS [API Gateway Resource](https://docs.aws.amazon.com/apigateway/api-reference/resource/resource/)."""

    label: str = "AWSAPIGatewayResource"
    # DEPRECATED: legacy APIGatewayResource node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([LEGACY_API_GATEWAY_RESOURCE])
    properties: APIGatewayResourceNodeProperties = APIGatewayResourceNodeProperties()
    sub_resource_relationship: APIGatewayResourceToAWSAccountRel = (
        APIGatewayResourceToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [APIGatewayResourceToRestAPIRel()],
    )
