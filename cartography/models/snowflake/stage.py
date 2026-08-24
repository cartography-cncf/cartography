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
from cartography.models.ontology.labels import FILE_STORAGE
from cartography.models.ontology.labels import OBJECT_STORAGE
from cartography.models.snowflake.extra_labels import SNOWFLAKE_SECURABLE


@dataclass(frozen=True)
class SnowflakeStageNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Account-scoped identifier for the stage."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="The stage name."
    )
    qualified_name: PropertyRef = PropertyRef(
        "qualified_name",
        extra_index=True,
        description="Fully qualified DATABASE.SCHEMA.NAME of the stage.",
    )
    database_name: PropertyRef = PropertyRef(
        "database_name", description="Name of the database containing the stage."
    )
    schema_name: PropertyRef = PropertyRef(
        "schema_name", description="Name of the schema containing the stage."
    )
    kind: PropertyRef = PropertyRef(
        "kind",
        description="Stage kind reported by Snowflake, for example PERMANENT or TEMPORARY.",
    )
    is_external: PropertyRef = PropertyRef(
        "is_external",
        description=(
            "String discriminator, 'true' or 'false', recording whether the stage points "
            "at customer-owned cloud storage rather than Snowflake-managed internal "
            "storage. Stored as a string because the conditional ObjectStorage and "
            "FileStorage ontology labels match on exact string values."
        ),
    )
    url: PropertyRef = PropertyRef(
        "url",
        extra_index=True,
        description=(
            "Cloud storage URL the external stage reads and writes. Null for an internal "
            "stage, whose files live in Snowflake-managed storage."
        ),
    )
    endpoint: PropertyRef = PropertyRef(
        "endpoint",
        description="S3-compatible or private endpoint the stage connects through.",
    )
    storage_integration: PropertyRef = PropertyRef(
        "storage_integration",
        description=(
            "Name of the storage integration that authenticates the stage. Null when the "
            "stage instead embeds its own credentials."
        ),
    )
    cloud: PropertyRef = PropertyRef(
        "cloud", description="Cloud provider hosting the stage's storage."
    )
    region: PropertyRef = PropertyRef(
        "region", description="Cloud region hosting the stage's storage."
    )
    has_credentials: PropertyRef = PropertyRef(
        "has_credentials",
        description=(
            "Whether the stage stores its own cloud credentials, which is a long-lived "
            "secret in the stage definition rather than a storage integration."
        ),
    )
    has_encryption_key: PropertyRef = PropertyRef(
        "has_encryption_key",
        description="Whether the stage carries a client-side encryption master key.",
    )
    directory_table: PropertyRef = PropertyRef(
        "directory_table",
        description="Whether a directory table is enabled over the stage's files.",
    )
    owner: PropertyRef = PropertyRef(
        "owner", description="Name of the role that owns the stage."
    )
    owner_role_type: PropertyRef = PropertyRef(
        "owner_role_type",
        description="Whether the owning role is an account ROLE or a DATABASE_ROLE.",
    )
    comment: PropertyRef = PropertyRef("comment", description="Stage comment.")
    created_on: PropertyRef = PropertyRef(
        "created_on", description="When the stage was created."
    )


@dataclass(frozen=True)
class SnowflakeStageToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeAccount)-[:RESOURCE]->(:SnowflakeStage)
class SnowflakeStageToAccountRel(CartographyRelSchema):
    """A Snowflake account contains the stage as a resource."""

    target_node_label: str = "SnowflakeAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SnowflakeStageToAccountRelProperties = (
        SnowflakeStageToAccountRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeStageToSchemaRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeSchema)-[:CONTAINS]->(:SnowflakeStage)
class SnowflakeStageToSchemaRel(CartographyRelSchema):
    """A Snowflake schema contains the stage."""

    target_node_label: str = "SnowflakeSchema"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("parent_schema_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: SnowflakeStageToSchemaRelProperties = (
        SnowflakeStageToSchemaRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeStageToStorageIntegrationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeStage)-[:USES_INTEGRATION]->(:SnowflakeStorageIntegration)
class SnowflakeStageToStorageIntegrationRel(CartographyRelSchema):
    """A Snowflake stage authenticates to cloud storage through a storage integration."""

    target_node_label: str = "SnowflakeStorageIntegration"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("storage_integration_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES_INTEGRATION"
    properties: SnowflakeStageToStorageIntegrationRelProperties = (
        SnowflakeStageToStorageIntegrationRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeStageToS3RelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeStage)-[:BACKED_BY]->(:AWSS3Bucket)
class SnowflakeStageToS3Rel(CartographyRelSchema):
    """A Snowflake external stage is backed by an Amazon S3 bucket."""

    target_node_label: str = "AWSS3Bucket"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"name": PropertyRef("s3_bucket")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "BACKED_BY"
    properties: SnowflakeStageToS3RelProperties = SnowflakeStageToS3RelProperties()


@dataclass(frozen=True)
class SnowflakeStageToGCSRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeStage)-[:BACKED_BY]->(:GCPBucket)
class SnowflakeStageToGCSRel(CartographyRelSchema):
    """A Snowflake external stage is backed by a Google Cloud Storage bucket."""

    target_node_label: str = "GCPBucket"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("gcs_bucket")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "BACKED_BY"
    properties: SnowflakeStageToGCSRelProperties = SnowflakeStageToGCSRelProperties()


@dataclass(frozen=True)
class SnowflakeStageToAzureStorageRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeStage)-[:BACKED_BY]->(:AzureStorageAccount)
class SnowflakeStageToAzureStorageRel(CartographyRelSchema):
    """A Snowflake external stage is backed by an Azure storage account."""

    target_node_label: str = "AzureStorageAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"name": PropertyRef("azure_storage_account")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "BACKED_BY"
    properties: SnowflakeStageToAzureStorageRelProperties = (
        SnowflakeStageToAzureStorageRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeStageSchema(CartographyNodeSchema):
    """Represents a Snowflake stage: the file location data is loaded from and unloaded to."""

    label: str = "SnowflakeStage"
    properties: SnowflakeStageNodeProperties = SnowflakeStageNodeProperties()
    # ObjectStorage / FileStorage: ontology labels, applied conditionally. An
    # external stage is a handle on a customer-owned object store, while an
    # internal stage is Snowflake-managed file storage; the two are materially
    # different exposures, so the discriminator decides which label applies.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        [
            SNOWFLAKE_SECURABLE,
            OBJECT_STORAGE.when(is_external="true"),
            FILE_STORAGE.when(is_external="false"),
        ],
    )
    sub_resource_relationship: SnowflakeStageToAccountRel = SnowflakeStageToAccountRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            SnowflakeStageToSchemaRel(),
            SnowflakeStageToStorageIntegrationRel(),
            SnowflakeStageToS3Rel(),
            SnowflakeStageToGCSRel(),
            SnowflakeStageToAzureStorageRel(),
        ],
    )
