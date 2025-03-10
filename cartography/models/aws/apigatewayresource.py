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
class APIGatewayResourceNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef('id')
    path: PropertyRef = PropertyRef('path')
    pathpart: PropertyRef = PropertyRef('pathPart')
    parentid: PropertyRef = PropertyRef('parentId')
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class APIGatewayResourceToRestAPIRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
# (:APIGatewayResource)<-[:RESOURCE]-(:APIGatewayRestAPI)
class APIGatewayResourceToRestAPI(CartographyRelSchema):
    target_node_label: str = 'APIGatewayRestAPI'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('apiId')},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: APIGatewayResourceToRestAPIRelProperties = APIGatewayResourceToRestAPIRelProperties()


@dataclass(frozen=True)
class APIGatewayResourceToAwsAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
# (:APIGatewayResource)<-[:RESOURCE]-(:AWSAccount)
class APIGatewayResourceToAWSAccount(CartographyRelSchema):
    target_node_label: str = 'AWSAccount'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('AWS_ID', set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: APIGatewayResourceToAwsAccountRelProperties = APIGatewayResourceToAwsAccountRelProperties()


@dataclass(frozen=True)
class APIGatewayResourceSchema(CartographyNodeSchema):
    label: str = 'APIGatewayResource'
    properties: APIGatewayResourceNodeProperties = APIGatewayResourceNodeProperties()
    sub_resource_relationship: APIGatewayResourceToAWSAccount = APIGatewayResourceToAWSAccount()
    other_relationships: OtherRelationships = OtherRelationships([APIGatewayResourceToRestAPI()])
