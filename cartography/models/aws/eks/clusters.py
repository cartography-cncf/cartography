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
class EKSClusterNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("arn")
    arn: PropertyRef = PropertyRef("arn", extra_index=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    created_at: PropertyRef = PropertyRef("created_at")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    endpoint: PropertyRef = PropertyRef("endpoint")
    endpoint_public_access: PropertyRef = PropertyRef("ClusterEndpointPublic")
    rolearn: PropertyRef = PropertyRef("roleArn")
    version: PropertyRef = PropertyRef("version")
    platform_version: PropertyRef = PropertyRef("platformVersion")
    status: PropertyRef = PropertyRef("status")
    audit_logging: PropertyRef = PropertyRef("ClusterLogging")
    certificate_authority_data_present: PropertyRef = PropertyRef(
        "certificate_authority_data_present",
    )
    certificate_authority_parse_status: PropertyRef = PropertyRef(
        "certificate_authority_parse_status",
    )
    certificate_authority_parse_error: PropertyRef = PropertyRef(
        "certificate_authority_parse_error",
    )
    certificate_authority_sha256_fingerprint: PropertyRef = PropertyRef(
        "certificate_authority_sha256_fingerprint",
        extra_index=True,
    )
    certificate_authority_subject: PropertyRef = PropertyRef(
        "certificate_authority_subject",
    )
    certificate_authority_issuer: PropertyRef = PropertyRef(
        "certificate_authority_issuer",
    )
    certificate_authority_not_before: PropertyRef = PropertyRef(
        "certificate_authority_not_before",
    )
    certificate_authority_not_after: PropertyRef = PropertyRef(
        "certificate_authority_not_after",
    )
    certificate_authority_subject_key_identifier: PropertyRef = PropertyRef(
        "certificate_authority_subject_key_identifier",
    )
    certificate_authority_authority_key_identifier: PropertyRef = PropertyRef(
        "certificate_authority_authority_key_identifier",
    )
    certificate_authority_expired: PropertyRef = PropertyRef(
        "certificate_authority_expired",
    )
    certificate_authority_days_until_expiry: PropertyRef = PropertyRef(
        "certificate_authority_days_until_expiry",
    )


@dataclass(frozen=True)
class EKSClusterToAWSAccountRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EKSClusterToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: EKSClusterToAWSAccountRelRelProperties = (
        EKSClusterToAWSAccountRelRelProperties()
    )


@dataclass(frozen=True)
class EKSClusterSchema(CartographyNodeSchema):
    label: str = "EKSCluster"
    properties: EKSClusterNodeProperties = EKSClusterNodeProperties()
    sub_resource_relationship: EKSClusterToAWSAccountRel = EKSClusterToAWSAccountRel()
