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
    id: PropertyRef = PropertyRef("clientCertificateId")
    createddate: PropertyRef = PropertyRef("createdDate")
    expirationdate: PropertyRef = PropertyRef("expirationDate")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class APIGatewayClientCertificateToStageRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class CertToStageRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:APIGatewayStage)-[:HAS_CERTIFICATE]->(:APIGatewayClientCertificate)
class APIGatewayClientCertificateToStageRel(CartographyRelSchema):
    target_node_label: str = "APIGatewayStage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("stageArn")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_CERTIFICATE"
    properties: CertToStageRelProperties = CertToStageRelProperties()


@dataclass(frozen=True)
class CertToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:APIGatewayClientCertificate)<-[:RESOURCE]-(:AWSAccount)
class APIGatewayClientCertificateToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: CertToAccountRelProperties = CertToAccountRelProperties()


@dataclass(frozen=True)
class APIGatewayClientCertificateSchema(CartographyNodeSchema):
    label: str = "APIGatewayClientCertificate"
    properties: APIGatewayClientCertificateNodeProperties = (
        APIGatewayClientCertificateNodeProperties()
    )
    sub_resource_relationship: APIGatewayClientCertificateToAWSAccountRel = (
        APIGatewayClientCertificateToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [APIGatewayClientCertificateToStageRel()],
    )
