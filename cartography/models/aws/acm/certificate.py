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
class ACMCertificateNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("Arn", description="The ARN of the certificate")
    arn: PropertyRef = PropertyRef(
        "Arn",
        extra_index=True,
        description="The Amazon Resource Name (ARN) of the certificate",
    )
    domainname: PropertyRef = PropertyRef(
        "DomainName", description="The primary domain name of the certificate"
    )
    type: PropertyRef = PropertyRef("Type", description="The source of the certificate")
    status: PropertyRef = PropertyRef(
        "Status", description="The status of the certificate"
    )
    key_algorithm: PropertyRef = PropertyRef(
        "KeyAlgorithm", description="The key algorithm used"
    )
    signature_algorithm: PropertyRef = PropertyRef(
        "SignatureAlgorithm", description="The signature algorithm"
    )
    not_before: PropertyRef = PropertyRef(
        "NotBefore", description="The time before which the certificate is invalid"
    )
    not_after: PropertyRef = PropertyRef(
        "NotAfter", description="The time after which the certificate expires"
    )
    in_use_by: PropertyRef = PropertyRef(
        "InUseBy", description="List of ARNs of resources that use this certificate"
    )
    region: PropertyRef = PropertyRef(
        "Region",
        set_in_kwargs=True,
        description="The AWS region where the certificate is located",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )


@dataclass(frozen=True)
class ACMCertificateToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ACMCertificateToAWSAccountRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSACMCertificate`."

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
    "Represents a `USED_BY` relationship from `AWSACMCertificate` to `AWSELBV2Listener`."

    target_node_label: str = "AWSELBV2Listener"
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
    "Represents an `AWSACMCertificate` node in the AWS graph."

    label: str = "AWSACMCertificate"
    # DEPRECATED: legacy ACMCertificate node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        ["ACMCertificate", "Certificate"]
    )
    properties: ACMCertificateNodeProperties = ACMCertificateNodeProperties()
    sub_resource_relationship: ACMCertificateToAWSAccountRel = (
        ACMCertificateToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [ACMCertificateToELBV2ListenerRel()]
    )
