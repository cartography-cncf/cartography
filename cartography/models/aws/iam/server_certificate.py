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
class AWSServerCertificateNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("ServerCertificateId")
    arn: PropertyRef = PropertyRef("Arn", extra_index=True)
    server_certificate_id: PropertyRef = PropertyRef(
        "ServerCertificateId", extra_index=True
    )
    server_certificate_name: PropertyRef = PropertyRef(
        "ServerCertificateName", extra_index=True
    )
    path: PropertyRef = PropertyRef("Path")
    expiration: PropertyRef = PropertyRef("Expiration")
    upload_date: PropertyRef = PropertyRef("UploadDate")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSServerCertificateToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSServerCertificateToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AWSServerCertificateToAWSAccountRelProperties = (
        AWSServerCertificateToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class AWSServerCertificateSchema(CartographyNodeSchema):
    label: str = "AWSServerCertificate"
    properties: AWSServerCertificateNodeProperties = (
        AWSServerCertificateNodeProperties()
    )
    sub_resource_relationship: AWSServerCertificateToAWSAccountRel = (
        AWSServerCertificateToAWSAccountRel()
    )
