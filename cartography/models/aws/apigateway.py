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
class APIGatewayRestAPINodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef('id', extra_index=True)
    createddate: PropertyRef = PropertyRef('createdDate')
    version: PropertyRef = PropertyRef('version')
    minimumcompressionsize: PropertyRef = PropertyRef('minimumCompressionSize')
    disableexecuteapiendpoint: PropertyRef = PropertyRef('disableExecuteApiEndpoint')
    region: PropertyRef = PropertyRef('region', set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)
    anonymous_access: PropertyRef = PropertyRef('anonymous_access')
    anonymous_actions: PropertyRef = PropertyRef('anonymous_actions')


@dataclass(frozen=True)
class APIGatewayRestAPIToAwsAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
# (:APIGatewayRestAPI)<-[:RESOURCE]-(:AWSAccount)
class APIGatewayRestAPIToAWSAccount(CartographyRelSchema):
    target_node_label: str = 'AWSAccount'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('AWS_ID', set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: APIGatewayRestAPIToAwsAccountRelProperties = APIGatewayRestAPIToAwsAccountRelProperties()


@dataclass(frozen=True)
class APIGatewayRestAPISchema(CartographyNodeSchema):
    label: str = 'APIGatewayRestAPI'
    properties: APIGatewayRestAPINodeProperties = APIGatewayRestAPINodeProperties()
    sub_resource_relationship: APIGatewayRestAPIToAWSAccount = APIGatewayRestAPIToAWSAccount()
