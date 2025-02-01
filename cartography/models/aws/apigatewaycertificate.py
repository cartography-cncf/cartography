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
class APIGatewayClientCertificateNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef('clientCertificateId')
    createddate: PropertyRef = PropertyRef('createdDate')
    expirationdate: PropertyRef = PropertyRef('expirationDate')
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class APIGatewayClientCertificateToStageRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
# (:APIGatewayStage)-[:HAS_CERTIFICATE]->(:APIGatewayClientCertificate)
class APIGatewayClientCertificateToStage(CartographyRelSchema):
    target_node_label: str = 'APIGatewayStage'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('stageArn')},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_CERTIFICATE"
    properties: APIGatewayClientCertificateToStageRelProperties = APIGatewayClientCertificateToStageRelProperties()


@dataclass(frozen=True)
class APIGatewayClientCertificateSchema(CartographyNodeSchema):
    label: str = 'APIGatewayClientCertificate'
    properties: APIGatewayClientCertificateNodeProperties = APIGatewayClientCertificateNodeProperties()
    other_relationships: OtherRelationships = OtherRelationships([APIGatewayClientCertificateToStage()])
