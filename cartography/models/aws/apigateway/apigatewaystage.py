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
class APIGatewayStageNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("arn", description="The ARN of the API Gateway Stage")
    stagename: PropertyRef = PropertyRef(
        "stageName", description="The name of the API Gateway Stage"
    )
    createddate: PropertyRef = PropertyRef(
        "createdDate", description="The timestamp when the stage was created"
    )
    deploymentid: PropertyRef = PropertyRef(
        "deploymentId",
        description="The identifier of the Deployment that the stage points to.",
    )
    clientcertificateid: PropertyRef = PropertyRef(
        "clientCertificateId",
        description="The identifier of a client certificate for an API stage.",
    )
    cacheclusterenabled: PropertyRef = PropertyRef(
        "cacheClusterEnabled",
        description="Specifies whether a cache cluster is enabled for the stage.",
    )
    cacheclusterstatus: PropertyRef = PropertyRef(
        "cacheClusterStatus",
        description="The status of the cache cluster for the stage, if enabled.",
    )
    tracingenabled: PropertyRef = PropertyRef(
        "tracingEnabled",
        description="Specifies whether active tracing with X-ray is enabled for the Stage",
    )
    webaclarn: PropertyRef = PropertyRef(
        "webAclArn", description="The ARN of the WebAcl associated with the Stage"
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )


@dataclass(frozen=True)
class APIGatewayStageToRestAPIRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AWSAPIGatewayStage)<-[:ASSOCIATED_WITH]-(:AWSAPIGatewayRestAPI)
class APIGatewayStageToRestAPIRel(CartographyRelSchema):
    "Represents a `ASSOCIATED_WITH` relationship from `AWSAPIGatewayRestAPI` to `AWSAPIGatewayStage`."

    target_node_label: str = "AWSAPIGatewayRestAPI"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("apiId")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "ASSOCIATED_WITH"
    properties: APIGatewayStageToRestAPIRelRelProperties = (
        APIGatewayStageToRestAPIRelRelProperties()
    )


@dataclass(frozen=True)
class APIGatewayStageToAWSAccountRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AWSAPIGatewayStage)<-[:RESOURCE]-(:AWSAccount)
class APIGatewayStageToAWSAccountRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSAPIGatewayStage`."

    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: APIGatewayStageToAWSAccountRelRelProperties = (
        APIGatewayStageToAWSAccountRelRelProperties()
    )


@dataclass(frozen=True)
class APIGatewayStageSchema(CartographyNodeSchema):
    "Represents an `AWSAPIGatewayStage` node in the AWS graph."

    label: str = "AWSAPIGatewayStage"
    # DEPRECATED: legacy APIGatewayStage node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["APIGatewayStage"])
    properties: APIGatewayStageNodeProperties = APIGatewayStageNodeProperties()
    sub_resource_relationship: APIGatewayStageToAWSAccountRel = (
        APIGatewayStageToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [APIGatewayStageToRestAPIRel()],
    )
