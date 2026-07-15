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
class APIGatewayDeploymentNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="The identifier for the deployment resource as string of api id and deployment id",
    )
    arn: PropertyRef = PropertyRef(
        "id",
        extra_index=True,
        description="The identifier for the deployment resource.",
    )
    description: PropertyRef = PropertyRef(
        "description", description="The description for the deployment resource."
    )
    region: PropertyRef = PropertyRef(
        "region",
        set_in_kwargs=True,
        description="The region for the deployment resource.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )


@dataclass(frozen=True)
class APIGatewayDeploymentToAWSAccountRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AWSAPIGatewayDeployment)<-[:RESOURCE]-(:AWSAccount)
class APIGatewayDeploymentToAWSAccountRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSAPIGatewayDeployment`."

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
# (:AWSAPIGatewayDeployment)<-[:HAS_DEPLOYMENT]-(:AWSAPIGatewayRestAPI)
class APIGatewayDeploymentToRestAPIRel(CartographyRelSchema):
    "Represents a `HAS_DEPLOYMENT` relationship from `AWSAPIGatewayRestAPI` to `AWSAPIGatewayDeployment`."

    target_node_label: str = "AWSAPIGatewayRestAPI"
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
    "Represents an `AWSAPIGatewayDeployment` node in the AWS graph."

    label: str = "AWSAPIGatewayDeployment"
    # DEPRECATED: legacy APIGatewayDeployment node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["APIGatewayDeployment"])
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
