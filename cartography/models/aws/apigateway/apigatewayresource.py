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
class APIGatewayResourceNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    path: PropertyRef = PropertyRef("path")
    pathpart: PropertyRef = PropertyRef("pathPart")
    parentid: PropertyRef = PropertyRef("parentId")
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
    label: str = "AWSAPIGatewayResource"
    # DEPRECATED: legacy APIGatewayResource node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["APIGatewayResource"])
    properties: APIGatewayResourceNodeProperties = APIGatewayResourceNodeProperties()
    sub_resource_relationship: APIGatewayResourceToAWSAccountRel = (
        APIGatewayResourceToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [APIGatewayResourceToRestAPIRel()],
    )
