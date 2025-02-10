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
class APIGatewayStageNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef('arn')
    stagename: PropertyRef = PropertyRef('stageName')
    createddate: PropertyRef = PropertyRef('createdDate')
    deploymentid: PropertyRef = PropertyRef('deploymentId')
    clientcertificateid: PropertyRef = PropertyRef('clientCertificateId')
    cacheclusterenabled: PropertyRef = PropertyRef('cacheClusterEnabled')
    cacheclusterstatus: PropertyRef = PropertyRef('cacheClusterStatus')
    tracingenabled: PropertyRef = PropertyRef('tracingEnabled')
    webaclarn: PropertyRef = PropertyRef('webAclArn')
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class APIGatewayStageToRestAPIRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
# (:APIGatewayStage)<-[:ASSOCIATED_WITH]-(:APIGatewayRestAPI)
class APIGatewayStageToRestAPI(CartographyRelSchema):
    target_node_label: str = 'APIGatewayRestAPI'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('apiId')},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "ASSOCIATED_WITH"
    properties: APIGatewayStageToRestAPIRelProperties = APIGatewayStageToRestAPIRelProperties()


@dataclass(frozen=True)
class APIGatewayStageToAwsAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
# (:APIGatewayStage)<-[:RESOURCE]-(:AWSAccount)
class APIGatewayStageToAWSAccount(CartographyRelSchema):
    target_node_label: str = 'AWSAccount'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('AWS_ID', set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: APIGatewayStageToAwsAccountRelProperties = APIGatewayStageToAwsAccountRelProperties()


@dataclass(frozen=True)
class APIGatewayStageSchema(CartographyNodeSchema):
    label: str = 'APIGatewayStage'
    properties: APIGatewayStageNodeProperties = APIGatewayStageNodeProperties()
    sub_resource_relationship: APIGatewayStageToAWSAccount = APIGatewayStageToAWSAccount()
    other_relationships: OtherRelationships = OtherRelationships([APIGatewayStageToRestAPI()])
