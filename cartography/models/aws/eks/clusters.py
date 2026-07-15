from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class EKSClusterNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("arn", description="same as `arn`")
    arn: PropertyRef = PropertyRef(
        "arn", extra_index=True, description="AWS-unique identifier for this object"
    )
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Name of the EKS Cluster"
    )
    region: PropertyRef = PropertyRef(
        "Region", set_in_kwargs=True, description="The AWS region"
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="The date and time the cluster was created"
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )
    endpoint: PropertyRef = PropertyRef(
        "endpoint", description="The endpoint for the Kubernetes API server."
    )
    endpoint_public_access: PropertyRef = PropertyRef(
        "ClusterEndpointPublic",
        extra_index=True,
        description="Indicates whether the Amazon EKS public API server endpoint is enabled",
    )  # Populated from sync input and read by aws_eks_asset_exposure.json.
    exposed_internet: PropertyRef = PropertyRef(
        "exposed_internet",
        extra_index=True,
        description="Set to True if the EKS Cluster public API server endpoint is enabled",
    )  # Populated by aws_eks_asset_exposure.json.
    rolearn: PropertyRef = PropertyRef(
        "roleArn",
        description="The ARN of the IAM role that provides permissions for the Kubernetes control plane to make calls to AWS API",
    )
    version: PropertyRef = PropertyRef(
        "version", description="Kubernetes version running"
    )
    platform_version: PropertyRef = PropertyRef(
        "platformVersion", description="Version of EKS"
    )
    status: PropertyRef = PropertyRef(
        "status",
        description="Status of the cluster. Valid Values: creating, active, deleting, failed, updating",
    )
    audit_logging: PropertyRef = PropertyRef(
        "ClusterLogging", description="Whether audit logging is enabled"
    )
    certificate_authority_data_present: PropertyRef = PropertyRef(
        "certificate_authority_data_present",
        description="Whether the EKS API server certificate authority data was returned by AWS",
    )
    certificate_authority_parse_status: PropertyRef = PropertyRef(
        "certificate_authority_parse_status",
        description="Parse status of the certificate authority data (`parsed`, `missing`, `invalid_base64`, `invalid_certificate`)",
    )
    certificate_authority_parse_error: PropertyRef = PropertyRef(
        "certificate_authority_parse_error",
        description="Parse/decode error message when certificate authority data cannot be parsed",
    )
    certificate_authority_sha256_fingerprint: PropertyRef = PropertyRef(
        "certificate_authority_sha256_fingerprint",
        extra_index=True,
        description="SHA256 fingerprint of the decoded EKS API server certificate authority certificate",
    )
    certificate_authority_subject: PropertyRef = PropertyRef(
        "certificate_authority_subject",
        description="Subject DN of the EKS API server certificate authority certificate",
    )
    certificate_authority_issuer: PropertyRef = PropertyRef(
        "certificate_authority_issuer",
        description="Issuer DN of the EKS API server certificate authority certificate",
    )
    certificate_authority_not_before: PropertyRef = PropertyRef(
        "certificate_authority_not_before",
        description="Certificate validity start time (Neo4j datetime)",
    )
    certificate_authority_not_after: PropertyRef = PropertyRef(
        "certificate_authority_not_after",
        description="Certificate validity end time (Neo4j datetime)",
    )
    certificate_authority_subject_key_identifier: PropertyRef = PropertyRef(
        "certificate_authority_subject_key_identifier",
        description="Subject Key Identifier (SKI) extension value in hex if present. `null` when the extension is absent (not derived from the public key)",
    )
    certificate_authority_authority_key_identifier: PropertyRef = PropertyRef(
        "certificate_authority_authority_key_identifier",
        description="Authority Key Identifier (AKI) extension key identifier value in hex if present. `null` when the extension or key identifier is absent",
    )


@dataclass(frozen=True)
class EKSClusterToAWSAccountRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EKSClusterToAWSAccountRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSEKSCluster`."

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
    "Represents an `AWSEKSCluster` node in the AWS graph."

    label: str = "AWSEKSCluster"
    # DEPRECATED: legacy EKSCluster node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        ["EKSCluster", "ComputeCluster"]
    )
    properties: EKSClusterNodeProperties = EKSClusterNodeProperties()
    sub_resource_relationship: EKSClusterToAWSAccountRel = EKSClusterToAWSAccountRel()
