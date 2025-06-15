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
class ACMCertificateNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("Arn")
    arn: PropertyRef = PropertyRef("Arn", extra_index=True)
    domainname: PropertyRef = PropertyRef("DomainName")
    type: PropertyRef = PropertyRef("Type")
    status: PropertyRef = PropertyRef("Status")
    key_algorithm: PropertyRef = PropertyRef("KeyAlgorithm")
    signature_algorithm: PropertyRef = PropertyRef("SignatureAlgorithm")
    not_before: PropertyRef = PropertyRef("NotBefore")
    not_after: PropertyRef = PropertyRef("NotAfter")
    in_use_by: PropertyRef = PropertyRef("InUseBy")
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ACMCertificateToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ACMCertificateToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ACMCertificateToAWSAccountRelProperties = (
        ACMCertificateToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class ACMCertificateToELBV2ListenerRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ACMCertificateToELBV2ListenerRel(CartographyRelSchema):
    target_node_label: str = "ELBV2Listener"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ELBV2ListenerArns", one_to_many=True)}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USED_BY"
    properties: ACMCertificateToELBV2ListenerRelProperties = (
        ACMCertificateToELBV2ListenerRelProperties()
    )


@dataclass(frozen=True)
class ACMCertificateSchema(CartographyNodeSchema):
    label: str = "ACMCertificate"
    properties: ACMCertificateNodeProperties = ACMCertificateNodeProperties()
    sub_resource_relationship: ACMCertificateToAWSAccountRel = (
        ACMCertificateToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [ACMCertificateToELBV2ListenerRel()]
    )
