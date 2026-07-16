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
    id: PropertyRef = PropertyRef("arn")
    stagename: PropertyRef = PropertyRef("stageName")
    createddate: PropertyRef = PropertyRef("createdDate")
    deploymentid: PropertyRef = PropertyRef("deploymentId")
    clientcertificateid: PropertyRef = PropertyRef("clientCertificateId")
    cacheclusterenabled: PropertyRef = PropertyRef("cacheClusterEnabled")
    cacheclusterstatus: PropertyRef = PropertyRef("cacheClusterStatus")
    tracingenabled: PropertyRef = PropertyRef("tracingEnabled")
    webaclarn: PropertyRef = PropertyRef("webAclArn")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class APIGatewayStageToRestAPIRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AWSAPIGatewayStage)<-[:ASSOCIATED_WITH]-(:AWSAPIGatewayRestAPI)
class APIGatewayStageToRestAPIRel(CartographyRelSchema):
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
