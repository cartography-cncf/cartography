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
class SentraDataStoreNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Sentra data store ID.")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp when this Sentra data store was last seen.",
    )
    name: PropertyRef = PropertyRef(
        "name",
        extra_index=True,
        description="Data store name as shown in Sentra.",
    )
    description: PropertyRef = PropertyRef(
        "description",
        description="Data store description.",
    )
    native_unique_id: PropertyRef = PropertyRef(
        "native_unique_id",
        extra_index=True,
        description="Provider-native identifier of the data store, as reported by Sentra.",
    )
    category: PropertyRef = PropertyRef(
        "category",
        description="Data store category, for example `RDBMS`, `NoSQL`, or `Object Storage`.",
    )
    hosting_service: PropertyRef = PropertyRef(
        "hosting_service",
        extra_index=True,
        description="Service hosting the data store, for example `s3` or `rds`.",
    )
    database_engine: PropertyRef = PropertyRef(
        "database_engine",
        description="Database engine, for example `postgres` or `mysql`.",
    )
    database_engine_version: PropertyRef = PropertyRef(
        "database_engine_version",
        description="Database engine version.",
    )
    region: PropertyRef = PropertyRef(
        "region",
        description="Cloud region of the data store.",
    )
    storage_account: PropertyRef = PropertyRef(
        "storage_account",
        description="Azure storage account that holds the data store.",
    )
    connector_id: PropertyRef = PropertyRef(
        "connector_id",
        description="ID of the Sentra connector that discovered the data store.",
    )
    connector_name: PropertyRef = PropertyRef(
        "connector_name",
        description="Display name of the Sentra connector that discovered the data store.",
    )
    connector_account_id: PropertyRef = PropertyRef(
        "connector_account_id",
        extra_index=True,
        description="Cloud or SaaS account ID of the connector, for example an AWS account ID.",
    )
    connector_account_type: PropertyRef = PropertyRef(
        "connector_account_type",
        description="Connector account type, for example `AWS`, `GCP`, `AZURE`, or `SNOWFLAKE`.",
    )
    connector_environment: PropertyRef = PropertyRef(
        "connector_environment",
        description="Connector environment, for example `production`.",
    )
    sensitivity_level: PropertyRef = PropertyRef(
        "sensitivity_level",
        extra_index=True,
        description="Sentra sensitivity level. `0` means that the store holds no sensitive data, and higher values mean more sensitive data.",
    )
    sensitivity_score: PropertyRef = PropertyRef(
        "sensitivity_score",
        description="Sentra sensitivity score.",
    )
    public_access_level: PropertyRef = PropertyRef(
        "public_access_level",
        description="Public access level: `private`, `public`, `can_be_public`, or `unknown`.",
    )
    is_encrypted: PropertyRef = PropertyRef(
        "is_encrypted",
        description="Whether the data store is encrypted at rest.",
    )
    is_encrypted_in_transit: PropertyRef = PropertyRef(
        "is_encrypted_in_transit",
        description="Whether the data store is encrypted in transit.",
    )
    encryption_method: PropertyRef = PropertyRef(
        "encryption_method",
        description="Cloud-prefixed encryption method, for example `S3:SSE-KMS`.",
    )
    is_backed_up: PropertyRef = PropertyRef(
        "is_backed_up",
        description="Whether backups are enabled for the data store.",
    )
    is_logging_enabled: PropertyRef = PropertyRef(
        "is_logging_enabled",
        description="Whether logging is enabled for the data store.",
    )
    is_managed: PropertyRef = PropertyRef(
        "is_managed",
        description="Whether the data store is a managed service.",
    )
    scan_status: PropertyRef = PropertyRef(
        "scan_status",
        description="Current Sentra scan status.",
    )
    last_scan_status: PropertyRef = PropertyRef(
        "last_scan_status",
        description="Status of the most recent Sentra scan.",
    )
    last_scanned: PropertyRef = PropertyRef(
        "last_scanned",
        description="Timestamp of the most recent Sentra scan.",
    )
    last_classified: PropertyRef = PropertyRef(
        "last_classified",
        description="Timestamp when Sentra last classified the data store.",
    )
    last_activity: PropertyRef = PropertyRef(
        "last_activity",
        description="Timestamp when the data in the store was last accessed.",
    )
    last_modified: PropertyRef = PropertyRef(
        "last_modified",
        description="Timestamp when the data store was last modified.",
    )
    created_at: PropertyRef = PropertyRef(
        "created_at",
        description="Timestamp when the data store was created in the source system.",
    )
    used_storage: PropertyRef = PropertyRef(
        "used_storage",
        description="Used storage in bytes.",
    )
    findings_count: PropertyRef = PropertyRef(
        "findings_count",
        description="Number of sensitive data findings in the data store.",
    )
    alerts_count: PropertyRef = PropertyRef(
        "alerts_count",
        description="Number of Sentra alerts on the data store.",
    )


@dataclass(frozen=True)
class SentraDataStoreToTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class SentraDataStoreToTenantRel(CartographyRelSchema):
    """The Sentra organization that discovered the data store."""

    target_node_label: str = "SentraTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TENANT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SentraDataStoreToTenantRelProperties = (
        SentraDataStoreToTenantRelProperties()
    )


@dataclass(frozen=True)
class SentraDataStoreToDataClassRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class SentraDataStoreToDataClassRel(CartographyRelSchema):
    """A kind of sensitive data that Sentra found in the data store."""

    target_node_label: str = "SentraDataClass"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("data_class_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "CONTAINS"
    properties: SentraDataStoreToDataClassRelProperties = (
        SentraDataStoreToDataClassRelProperties()
    )


@dataclass(frozen=True)
class SentraDataStoreToCloudResourceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# Sentra names the cloud resource behind a data store only through
# `native_unique_id` and the store name. The transform extracts each provider ID
# below only when its shape proves the resource type, so a data store never links
# to a resource of a different kind.


@dataclass(frozen=True)
class SentraDataStoreToS3BucketRel(CartographyRelSchema):
    """The S3 bucket that the data store represents, matched on the bucket name from an S3 ARN or from the name of an `s3` store in an AWS account."""

    target_node_label: str = "AWSS3Bucket"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("aws_s3_bucket_name")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MONITORS"
    properties: SentraDataStoreToCloudResourceRelProperties = (
        SentraDataStoreToCloudResourceRelProperties()
    )


@dataclass(frozen=True)
class SentraDataStoreToRDSInstanceRel(CartographyRelSchema):
    """The RDS DB instance that the data store represents, matched on the instance ARN."""

    target_node_label: str = "AWSRDSInstance"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("aws_rds_instance_arn")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MONITORS"
    properties: SentraDataStoreToCloudResourceRelProperties = (
        SentraDataStoreToCloudResourceRelProperties()
    )


@dataclass(frozen=True)
class SentraDataStoreToRDSClusterRel(CartographyRelSchema):
    """The RDS DB cluster that the data store represents, matched on the cluster ARN."""

    target_node_label: str = "AWSRDSCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("aws_rds_cluster_arn")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MONITORS"
    properties: SentraDataStoreToCloudResourceRelProperties = (
        SentraDataStoreToCloudResourceRelProperties()
    )


@dataclass(frozen=True)
class SentraDataStoreToDynamoDBTableRel(CartographyRelSchema):
    """The DynamoDB table that the data store represents, matched on the table ARN."""

    target_node_label: str = "AWSDynamoDBTable"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("aws_dynamodb_table_arn")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MONITORS"
    properties: SentraDataStoreToCloudResourceRelProperties = (
        SentraDataStoreToCloudResourceRelProperties()
    )


@dataclass(frozen=True)
class SentraDataStoreToRedshiftClusterRel(CartographyRelSchema):
    """The Redshift cluster that the data store represents, matched on the cluster ARN."""

    target_node_label: str = "AWSRedshiftCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("aws_redshift_cluster_arn")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MONITORS"
    properties: SentraDataStoreToCloudResourceRelProperties = (
        SentraDataStoreToCloudResourceRelProperties()
    )


@dataclass(frozen=True)
class SentraDataStoreSchema(CartographyNodeSchema):
    """
    A data store that Sentra discovered and classified, such as an S3 bucket, a database, or a SaaS drive.

    The node is Sentra's view of the store: its sensitivity, the data classes found in it,
    and its security posture. Where Sentra's identifier proves which AWS resource the store
    is, the node links to that resource with `MONITORS`. Data stores in other clouds and in
    SaaS applications have no `MONITORS` link.
    """

    label: str = "SentraDataStore"
    properties: SentraDataStoreNodeProperties = SentraDataStoreNodeProperties()
    sub_resource_relationship: SentraDataStoreToTenantRel = SentraDataStoreToTenantRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            SentraDataStoreToDataClassRel(),
            SentraDataStoreToS3BucketRel(),
            SentraDataStoreToRDSInstanceRel(),
            SentraDataStoreToRDSClusterRel(),
            SentraDataStoreToDynamoDBTableRel(),
            SentraDataStoreToRedshiftClusterRel(),
        ],
    )
