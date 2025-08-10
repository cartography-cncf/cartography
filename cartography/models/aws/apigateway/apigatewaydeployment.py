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
class APIGatewayDeploymentNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    arn: PropertyRef = PropertyRef("id", extra_index=True)
    description: PropertyRef = PropertyRef("description")
    region: PropertyRef = PropertyRef("region", set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class APIGatewayDeploymentToAWSAccountRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:APIGatewayDeployment)<-[:RESOURCE]-(:AWSAccount)
class APIGatewayDeploymentToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: APIGatewayDeploymentToAWSAccountRelRelProperties = (
        APIGatewayDeploymentToAWSAccountRelRelProperties()
    )


@dataclass(frozen=True)
class APIGatewayDeploymentToRestAPIRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:APIGatewayDeployment)<-[:HAS_DEPLOYMENT]-(:APIGatewayRestAPI)
class APIGatewayDeploymentToRestAPIRel(CartographyRelSchema):
    target_node_label: str = "APIGatewayRestAPI"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("api_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_DEPLOYMENT"
    properties: APIGatewayDeploymentToRestAPIRelRelProperties = (
        APIGatewayDeploymentToRestAPIRelRelProperties()
    )


@dataclass(frozen=True)
class APIGatewayDeploymentSchema(CartographyNodeSchema):
    label: str = "APIGatewayDeployment"
    properties: APIGatewayDeploymentNodeProperties = (
        APIGatewayDeploymentNodeProperties()
    )
    sub_resource_relationship: APIGatewayDeploymentToAWSAccountRel = (
        APIGatewayDeploymentToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            APIGatewayDeploymentToRestAPIRel(),
        ]
    )
