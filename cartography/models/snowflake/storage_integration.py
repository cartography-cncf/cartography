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
from cartography.models.snowflake.extra_labels import SNOWFLAKE_SECURABLE


@dataclass(frozen=True)
class SnowflakeStorageIntegrationNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Account-scoped identifier for the storage integration."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="The storage integration name."
    )
    integration_type: PropertyRef = PropertyRef(
        "integration_type",
        description="Snowflake integration type, for example EXTERNAL_STAGE.",
    )
    category: PropertyRef = PropertyRef(
        "category", description="Snowflake integration category."
    )
    enabled: PropertyRef = PropertyRef(
        "enabled",
        description="Whether stages may authenticate to cloud storage through the integration.",
    )
    storage_provider: PropertyRef = PropertyRef(
        "storage_provider",
        description="Cloud storage provider: S3, S3GOV, GCS or AZURE.",
    )
    storage_allowed_locations: PropertyRef = PropertyRef(
        "storage_allowed_locations",
        description=(
            "Storage URL prefixes stages using this integration may read and write. A "
            "bare bucket prefix grants the whole bucket."
        ),
    )
    storage_blocked_locations: PropertyRef = PropertyRef(
        "storage_blocked_locations",
        description="Storage URL prefixes denied even when covered by an allowed location.",
    )
    storage_aws_role_arn: PropertyRef = PropertyRef(
        "storage_aws_role_arn",
        extra_index=True,
        description="ARN of the AWS IAM role Snowflake assumes to reach the storage.",
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
        description="Entra ID tenant Snowflake requests an access token from for the storage.",
    )
    azure_multi_tenant_app_name: PropertyRef = PropertyRef(
        "azure_multi_tenant_app_name",
        description=(
            "Name of the Snowflake multi-tenant Entra ID application that must be "
            "granted access to the storage account."
        ),
    )
    use_privatelink_endpoint: PropertyRef = PropertyRef(
        "use_privatelink_endpoint",
        description="Whether traffic to the storage goes over a private endpoint.",
    )
    comment: PropertyRef = PropertyRef(
        "comment", description="Storage integration comment."
    )
    created_on: PropertyRef = PropertyRef(
        "created_on", description="When the storage integration was created."
    )


@dataclass(frozen=True)
class SnowflakeStorageIntegrationToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeAccount)-[:RESOURCE]->(:SnowflakeStorageIntegration)
class SnowflakeStorageIntegrationToAccountRel(CartographyRelSchema):
    """A Snowflake account contains the storage integration as a resource."""

    target_node_label: str = "SnowflakeAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SnowflakeStorageIntegrationToAccountRelProperties = (
        SnowflakeStorageIntegrationToAccountRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeStorageIntegrationToAWSPrincipalRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeStorageIntegration)-[:ASSUMES_ROLE]->(:AWSPrincipal)
class SnowflakeStorageIntegrationToAWSPrincipalRel(CartographyRelSchema):
    """A Snowflake storage integration assumes an AWS IAM role to reach cloud storage."""

    target_node_label: str = "AWSPrincipal"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("storage_aws_role_arn")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ASSUMES_ROLE"
    properties: SnowflakeStorageIntegrationToAWSPrincipalRelProperties = (
        SnowflakeStorageIntegrationToAWSPrincipalRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeStorageIntegrationSchema(CartographyNodeSchema):
    """Represents a Snowflake storage integration: the delegated cloud identity stages use instead of embedded credentials."""

    label: str = "SnowflakeStorageIntegration"
    properties: SnowflakeStorageIntegrationNodeProperties = (
        SnowflakeStorageIntegrationNodeProperties()
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([SNOWFLAKE_SECURABLE])
    sub_resource_relationship: SnowflakeStorageIntegrationToAccountRel = (
        SnowflakeStorageIntegrationToAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [SnowflakeStorageIntegrationToAWSPrincipalRel()],
    )
