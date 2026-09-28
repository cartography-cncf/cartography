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
class SnowflakeCatalogIntegrationNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Account-scoped identifier for the catalog integration."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="The catalog integration name."
    )
    enabled: PropertyRef = PropertyRef(
        "enabled",
        description="Whether Iceberg tables may be created against the catalog.",
    )
    integration_type: PropertyRef = PropertyRef(
        "integration_type",
        description="Snowflake integration type reported for the catalog integration.",
    )
    category: PropertyRef = PropertyRef(
        "category", description="Snowflake integration category."
    )
    table_format: PropertyRef = PropertyRef(
        "table_format",
        description="Open table format the catalog serves, for example ICEBERG.",
    )
    catalog_source: PropertyRef = PropertyRef(
        "catalog_source",
        description="Where table metadata is read from: GLUE, OBJECT_STORE or POLARIS.",
    )
    glue_aws_role_arn: PropertyRef = PropertyRef(
        "glue_aws_role_arn",
        extra_index=True,
        description="ARN of the AWS IAM role Snowflake assumes to read the Glue Data Catalog.",
    )
    glue_aws_iam_user_arn: PropertyRef = PropertyRef(
        "glue_aws_iam_user_arn",
        description=(
            "ARN of the Snowflake-owned IAM user that must be trusted by the role's "
            "trust policy."
        ),
    )
    glue_catalog_id: PropertyRef = PropertyRef(
        "glue_catalog_id",
        description="AWS account id owning the Glue Data Catalog being read.",
    )
    glue_region: PropertyRef = PropertyRef(
        "glue_region", description="AWS region of the Glue Data Catalog."
    )
    catalog_namespace: PropertyRef = PropertyRef(
        "catalog_namespace",
        description="Default namespace (Glue database or Iceberg namespace) tables resolve in.",
    )
    rest_catalog_uri: PropertyRef = PropertyRef(
        "rest_catalog_uri",
        description="Base URI of the Iceberg REST catalog, when the source is a REST catalog.",
    )
    rest_warehouse: PropertyRef = PropertyRef(
        "rest_warehouse",
        description="Warehouse identifier passed to the Iceberg REST catalog.",
    )
    rest_authentication_type: PropertyRef = PropertyRef(
        "rest_authentication_type",
        description="How Snowflake authenticates to the REST catalog, for example OAUTH or SIGV4.",
    )
    oauth_client_id: PropertyRef = PropertyRef(
        "oauth_client_id",
        description=(
            "OAuth client id used against the REST catalog. The matching client secret "
            "is deliberately never stored."
        ),
    )
    oauth_allowed_scopes: PropertyRef = PropertyRef(
        "oauth_allowed_scopes",
        description="OAuth scopes requested when authenticating to the REST catalog.",
    )
    comment: PropertyRef = PropertyRef(
        "comment", description="Catalog integration comment."
    )
    created_on: PropertyRef = PropertyRef(
        "created_on", description="When the catalog integration was created."
    )


@dataclass(frozen=True)
class SnowflakeCatalogIntegrationToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeAccount)-[:RESOURCE]->(:SnowflakeCatalogIntegration)
class SnowflakeCatalogIntegrationToAccountRel(CartographyRelSchema):
    """A Snowflake account contains the catalog integration as a resource."""

    target_node_label: str = "SnowflakeAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SnowflakeCatalogIntegrationToAccountRelProperties = (
        SnowflakeCatalogIntegrationToAccountRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeCatalogIntegrationToAWSPrincipalRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeCatalogIntegration)-[:ASSUMES_ROLE]->(:AWSPrincipal)
class SnowflakeCatalogIntegrationToAWSPrincipalRel(CartographyRelSchema):
    """A Snowflake catalog integration assumes an AWS IAM role to read the Glue Data Catalog."""

    target_node_label: str = "AWSPrincipal"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("glue_aws_role_arn")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ASSUMES_ROLE"
    properties: SnowflakeCatalogIntegrationToAWSPrincipalRelProperties = (
        SnowflakeCatalogIntegrationToAWSPrincipalRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeCatalogIntegrationSchema(CartographyNodeSchema):
    """Represents a Snowflake catalog integration: the external table catalog Iceberg tables resolve metadata through."""

    label: str = "SnowflakeCatalogIntegration"
    properties: SnowflakeCatalogIntegrationNodeProperties = (
        SnowflakeCatalogIntegrationNodeProperties()
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([SNOWFLAKE_SECURABLE])
    sub_resource_relationship: SnowflakeCatalogIntegrationToAccountRel = (
        SnowflakeCatalogIntegrationToAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [SnowflakeCatalogIntegrationToAWSPrincipalRel()],
    )
