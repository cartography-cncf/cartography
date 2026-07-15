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
class ECSClusterNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("clusterArn", description="The ARN of the cluster")
    arn: PropertyRef = PropertyRef(
        "clusterArn", extra_index=True, description="The ARN of the cluster"
    )
    name: PropertyRef = PropertyRef(
        "clusterName",
        description="A user-generated string that you use to identify your cluster.",
    )
    region: PropertyRef = PropertyRef(
        "Region", set_in_kwargs=True, description="The region of the cluster."
    )
    status: PropertyRef = PropertyRef("status", description="The status of the cluster")
    ecc_kms_key_id: PropertyRef = PropertyRef(
        "ecc_kms_key_id",
        description="An AWS Key Management Service key ID to encrypt the data between the local client and the container.",
    )
    ecc_logging: PropertyRef = PropertyRef(
        "ecc_logging",
        description="The log setting to use for redirecting logs for your execute command results.",
    )
    ecc_log_configuration_cloud_watch_log_group_name: PropertyRef = PropertyRef(
        "ecc_log_configuration_cloud_watch_log_group_name",
        description="The name of the CloudWatch log group to send logs to.",
    )
    ecc_log_configuration_cloud_watch_encryption_enabled: PropertyRef = PropertyRef(
        "ecc_log_configuration_cloud_watch_encryption_enabled",
        description="Determines whether to enable encryption on the CloudWatch logs.",
    )
    ecc_log_configuration_s3_bucket_name: PropertyRef = PropertyRef(
        "ecc_log_configuration_s3_bucket_name",
        description="The name of the S3 bucket to send logs to.",
    )
    ecc_log_configuration_s3_encryption_enabled: PropertyRef = PropertyRef(
        "ecc_log_configuration_s3_encryption_enabled",
        description="Determines whether to use encryption on the S3 logs.",
    )
    ecc_log_configuration_s3_key_prefix: PropertyRef = PropertyRef(
        "ecc_log_configuration_s3_key_prefix",
        description="An optional folder in the S3 bucket to place logs in.",
    )
    capacity_providers: PropertyRef = PropertyRef(
        "capacityProviders",
        description="The capacity providers associated with the cluster.",
    )
    attachments_status: PropertyRef = PropertyRef(
        "attachmentsStatus",
        description="The status of the capacity providers associated with the cluster.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )


@dataclass(frozen=True)
class ECSClusterToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ECSClusterToAWSAccountRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSECSCluster`."

    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ECSClusterToAWSAccountRelProperties = (
        ECSClusterToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class ECSClusterSchema(CartographyNodeSchema):
    "Represents an `AWSECSCluster` node in the AWS graph."

    label: str = "AWSECSCluster"
    # DEPRECATED: legacy ECSCluster node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        ["ECSCluster", "ComputeCluster"]
    )
    properties: ECSClusterNodeProperties = ECSClusterNodeProperties()
    sub_resource_relationship: ECSClusterToAWSAccountRel = ECSClusterToAWSAccountRel()
