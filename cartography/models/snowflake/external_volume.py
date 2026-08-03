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
from cartography.models.ontology.labels import OBJECT_STORAGE
from cartography.models.snowflake.extra_labels import SNOWFLAKE_SECURABLE


@dataclass(frozen=True)
class SnowflakeExternalVolumeNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Account-scoped identifier for the external volume."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="The external volume name."
    )
    allow_writes: PropertyRef = PropertyRef(
        "allow_writes",
        description=(
            "Whether Snowflake may write to the volume's storage locations, which is "
            "required for Snowflake-managed Iceberg tables."
        ),
    )
    storage_location_count: PropertyRef = PropertyRef(
        "storage_location_count",
        description="Number of storage locations configured on the volume.",
    )
    owner: PropertyRef = PropertyRef(
        "owner", description="Name of the role that owns the external volume."
    )
    owner_role_type: PropertyRef = PropertyRef(
        "owner_role_type",
        description="Whether the owning role is an account ROLE or a DATABASE_ROLE.",
    )
    comment: PropertyRef = PropertyRef(
        "comment", description="External volume comment."
    )
    created_on: PropertyRef = PropertyRef(
        "created_on", description="When the external volume was created."
    )


@dataclass(frozen=True)
class SnowflakeExternalVolumeToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeAccount)-[:RESOURCE]->(:SnowflakeExternalVolume)
class SnowflakeExternalVolumeToAccountRel(CartographyRelSchema):
    """A Snowflake account contains the external volume as a resource."""

    target_node_label: str = "SnowflakeAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SnowflakeExternalVolumeToAccountRelProperties = (
        SnowflakeExternalVolumeToAccountRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeExternalVolumeSchema(CartographyNodeSchema):
    """Represents a Snowflake external volume: the named set of cloud storage locations Iceberg tables are written to."""

    label: str = "SnowflakeExternalVolume"
    properties: SnowflakeExternalVolumeNodeProperties = (
        SnowflakeExternalVolumeNodeProperties()
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([SNOWFLAKE_SECURABLE])
    sub_resource_relationship: SnowflakeExternalVolumeToAccountRel = (
        SnowflakeExternalVolumeToAccountRel()
    )


@dataclass(frozen=True)
class SnowflakeExternalVolumeStorageLocationNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Account-scoped identifier for the external volume storage location.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name",
        extra_index=True,
        description="Name of the storage location within its external volume.",
    )
    volume_name: PropertyRef = PropertyRef(
        "volume_name", description="Name of the external volume that owns the location."
    )
    storage_provider: PropertyRef = PropertyRef(
        "storage_provider",
        description="Cloud storage provider: S3, S3GOV, GCS or AZURE.",
    )
    storage_base_url: PropertyRef = PropertyRef(
        "storage_base_url",
        extra_index=True,
        description="Base cloud storage URL that Iceberg data and metadata are written under.",
    )
    storage_aws_role_arn: PropertyRef = PropertyRef(
        "storage_aws_role_arn",
        extra_index=True,
        description="ARN of the AWS IAM role Snowflake assumes to reach the location.",
    )
    storage_aws_iam_user_arn: PropertyRef = PropertyRef(
        "storage_aws_iam_user_arn",
        description=(
            "ARN of the Snowflake-owned IAM user that must be trusted by the role's "
            "trust policy."
        ),
    )
    storage_aws_external_id: PropertyRef = PropertyRef(
        "storage_aws_external_id",
        description=(
            "External id the role's trust policy must require, which is what prevents "
            "another Snowflake account from assuming it."
        ),
    )
    azure_tenant_id: PropertyRef = PropertyRef(
        "azure_tenant_id",
        description="Entra ID tenant Snowflake requests an access token from for the location.",
    )
    encryption_type: PropertyRef = PropertyRef(
        "encryption_type",
        description=(
            "Server-side encryption applied to the location: NONE, AWS_SSE_S3, "
            "AWS_SSE_KMS or GCS_SSE_KMS."
        ),
    )
    kms_key_id: PropertyRef = PropertyRef(
        "kms_key_id",
        extra_index=True,
        description="Identifier of the KMS key used when encryption is customer-managed.",
    )
    s3_bucket: PropertyRef = PropertyRef(
        "s3_bucket",
        description="Name of the S3 bucket parsed out of the base URL, when the provider is AWS.",
    )
    gcs_bucket: PropertyRef = PropertyRef(
        "gcs_bucket",
        description="Name of the GCS bucket parsed out of the base URL, when the provider is GCS.",
    )
    azure_storage_account: PropertyRef = PropertyRef(
        "azure_storage_account",
        description=(
            "Name of the Azure storage account parsed out of the base URL, when the "
            "provider is Azure."
        ),
    )


@dataclass(frozen=True)
class SnowflakeStorageLocationToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeAccount)-[:RESOURCE]->(:SnowflakeExternalVolumeStorageLocation)
class SnowflakeStorageLocationToAccountRel(CartographyRelSchema):
    """A Snowflake account contains the external volume storage location as a resource."""

    target_node_label: str = "SnowflakeAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SnowflakeStorageLocationToAccountRelProperties = (
        SnowflakeStorageLocationToAccountRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeStorageLocationToVolumeRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeExternalVolume)-[:HAS_STORAGE_LOCATION]->(:SnowflakeExternalVolumeStorageLocation)
class SnowflakeStorageLocationToVolumeRel(CartographyRelSchema):
    """A Snowflake external volume writes to this storage location."""

    target_node_label: str = "SnowflakeExternalVolume"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("parent_volume_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_STORAGE_LOCATION"
    properties: SnowflakeStorageLocationToVolumeRelProperties = (
        SnowflakeStorageLocationToVolumeRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeStorageLocationToS3RelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeExternalVolumeStorageLocation)-[:BACKED_BY]->(:AWSS3Bucket)
class SnowflakeStorageLocationToS3Rel(CartographyRelSchema):
    """A Snowflake external volume storage location is backed by an Amazon S3 bucket."""

    target_node_label: str = "AWSS3Bucket"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"name": PropertyRef("s3_bucket")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "BACKED_BY"
    properties: SnowflakeStorageLocationToS3RelProperties = (
        SnowflakeStorageLocationToS3RelProperties()
    )


@dataclass(frozen=True)
class SnowflakeStorageLocationToGCSRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeExternalVolumeStorageLocation)-[:BACKED_BY]->(:GCPBucket)
class SnowflakeStorageLocationToGCSRel(CartographyRelSchema):
    """A Snowflake external volume storage location is backed by a Google Cloud Storage bucket."""

    target_node_label: str = "GCPBucket"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("gcs_bucket")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "BACKED_BY"
    properties: SnowflakeStorageLocationToGCSRelProperties = (
        SnowflakeStorageLocationToGCSRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeStorageLocationToAzureStorageRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeExternalVolumeStorageLocation)-[:BACKED_BY]->(:AzureStorageAccount)
class SnowflakeStorageLocationToAzureStorageRel(CartographyRelSchema):
    """A Snowflake external volume storage location is backed by an Azure storage account."""

    target_node_label: str = "AzureStorageAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"name": PropertyRef("azure_storage_account")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "BACKED_BY"
    properties: SnowflakeStorageLocationToAzureStorageRelProperties = (
        SnowflakeStorageLocationToAzureStorageRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeStorageLocationToKMSKeyRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeExternalVolumeStorageLocation)-[:ENCRYPTED_BY]->(:AWSKMSKey)
class SnowflakeStorageLocationToKMSKeyRel(CartographyRelSchema):
    """A Snowflake external volume storage location is encrypted with an AWS KMS key."""

    target_node_label: str = "AWSKMSKey"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("kms_key_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ENCRYPTED_BY"
    properties: SnowflakeStorageLocationToKMSKeyRelProperties = (
        SnowflakeStorageLocationToKMSKeyRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeStorageLocationToAWSPrincipalRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeExternalVolumeStorageLocation)-[:ASSUMES_ROLE]->(:AWSPrincipal)
class SnowflakeStorageLocationToAWSPrincipalRel(CartographyRelSchema):
    """A Snowflake external volume storage location assumes an AWS IAM role to reach its bucket."""

    target_node_label: str = "AWSPrincipal"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("storage_aws_role_arn")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ASSUMES_ROLE"
    properties: SnowflakeStorageLocationToAWSPrincipalRelProperties = (
        SnowflakeStorageLocationToAWSPrincipalRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeExternalVolumeStorageLocationSchema(CartographyNodeSchema):
    """Represents one cloud storage location of a Snowflake external volume."""

    label: str = "SnowflakeExternalVolumeStorageLocation"
    properties: SnowflakeExternalVolumeStorageLocationNodeProperties = (
        SnowflakeExternalVolumeStorageLocationNodeProperties()
    )
    # ObjectStorage: ontology label; a storage location is a path in an object store.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([OBJECT_STORAGE])
    sub_resource_relationship: SnowflakeStorageLocationToAccountRel = (
        SnowflakeStorageLocationToAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            SnowflakeStorageLocationToVolumeRel(),
            SnowflakeStorageLocationToS3Rel(),
            SnowflakeStorageLocationToGCSRel(),
            SnowflakeStorageLocationToAzureStorageRel(),
            SnowflakeStorageLocationToKMSKeyRel(),
            SnowflakeStorageLocationToAWSPrincipalRel(),
        ],
    )
