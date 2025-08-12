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
class ECSClusterNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("clusterArn")
    arn: PropertyRef = PropertyRef("clusterArn", extra_index=True)
    name: PropertyRef = PropertyRef("clusterName")
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    status: PropertyRef = PropertyRef("status")
    ecc_kms_key_id: PropertyRef = PropertyRef("ecc_kms_key_id")
    ecc_logging: PropertyRef = PropertyRef("ecc_logging")
    ecc_log_configuration_cloud_watch_log_group_name: PropertyRef = PropertyRef(
        "ecc_log_configuration_cloud_watch_log_group_name"
    )
    ecc_log_configuration_cloud_watch_encryption_enabled: PropertyRef = PropertyRef(
        "ecc_log_configuration_cloud_watch_encryption_enabled"
    )
    ecc_log_configuration_s3_bucket_name: PropertyRef = PropertyRef(
        "ecc_log_configuration_s3_bucket_name"
    )
    ecc_log_configuration_s3_encryption_enabled: PropertyRef = PropertyRef(
        "ecc_log_configuration_s3_encryption_enabled"
    )
    ecc_log_configuration_s3_key_prefix: PropertyRef = PropertyRef(
        "ecc_log_configuration_s3_key_prefix"
    )
    capacity_providers: PropertyRef = PropertyRef("capacityProviders")
    attachments_status: PropertyRef = PropertyRef("attachmentsStatus")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ECSClusterToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ECSClusterToAWSAccountRel(CartographyRelSchema):
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
    label: str = "ECSCluster"
    properties: ECSClusterNodeProperties = ECSClusterNodeProperties()
    sub_resource_relationship: ECSClusterToAWSAccountRel = ECSClusterToAWSAccountRel()
