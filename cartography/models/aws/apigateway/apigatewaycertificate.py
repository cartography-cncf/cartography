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
class APIGatewayClientCertificateNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "clientCertificateId", description="The identifier of the client certificate"
    )
    createddate: PropertyRef = PropertyRef(
        "createdDate",
        description="The timestamp when the client certificate was created",
    )
    expirationdate: PropertyRef = PropertyRef(
        "expirationDate",
        description="The timestamp when the client certificate will expire",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )


@dataclass(frozen=True)
class APIGatewayClientCertificateToStageRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class CertToStageRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AWSAPIGatewayStage)-[:HAS_CERTIFICATE]->(:AWSAPIGatewayClientCertificate)
class APIGatewayClientCertificateToStageRel(CartographyRelSchema):
    "Represents a `HAS_CERTIFICATE` relationship from `AWSAPIGatewayStage` to `AWSAPIGatewayClientCertificate`."

    target_node_label: str = "AWSAPIGatewayStage"
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
# (:AWSAPIGatewayClientCertificate)<-[:RESOURCE]-(:AWSAccount)
class APIGatewayClientCertificateToAWSAccountRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSAPIGatewayClientCertificate`."

    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: CertToAccountRelProperties = CertToAccountRelProperties()


@dataclass(frozen=True)
class APIGatewayClientCertificateSchema(CartographyNodeSchema):
    "Represents an `AWSAPIGatewayClientCertificate` node in the AWS graph."

    label: str = "AWSAPIGatewayClientCertificate"
    # DEPRECATED: legacy APIGatewayClientCertificate node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        ["APIGatewayClientCertificate"]
    )
    properties: APIGatewayClientCertificateNodeProperties = (
        APIGatewayClientCertificateNodeProperties()
    )
    sub_resource_relationship: APIGatewayClientCertificateToAWSAccountRel = (
        APIGatewayClientCertificateToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [APIGatewayClientCertificateToStageRel()],
    )
