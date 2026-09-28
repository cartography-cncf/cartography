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
class SnowflakeApiIntegrationNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Account-scoped identifier for the API integration."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="The API integration name."
    )
    enabled: PropertyRef = PropertyRef(
        "enabled",
        description="Whether the integration may be used by external functions and Git repositories.",
    )
    api_allowed_prefixes: PropertyRef = PropertyRef(
        "api_allowed_prefixes",
        description=(
            "URL prefixes external functions may call through the integration. A broad "
            "prefix lets any function in the account reach the whole endpoint tree."
        ),
    )
    api_blocked_prefixes: PropertyRef = PropertyRef(
        "api_blocked_prefixes",
        description="URL prefixes denied even when covered by an allowed prefix.",
    )
    api_hook_type: PropertyRef = PropertyRef(
        "api_hook_type",
        description="Backing platform of the integration: AWS, AZURE, GCP or GIT.",
    )
    api_provider: PropertyRef = PropertyRef(
        "api_provider",
        description=(
            "Concrete provider, for example aws_api_gateway, azure_api_management or "
            "git_https_api."
        ),
    )
    api_aws_role_arn: PropertyRef = PropertyRef(
        "api_aws_role_arn",
        extra_index=True,
        description="ARN of the AWS IAM role Snowflake assumes to invoke the API Gateway.",
    )
    api_aws_iam_user_arn: PropertyRef = PropertyRef(
        "api_aws_iam_user_arn",
        description=(
            "ARN of the Snowflake-owned IAM user that must be trusted by the role's "
            "trust policy."
        ),
    )
    api_aws_external_id: PropertyRef = PropertyRef(
        "api_aws_external_id",
        description=(
            "External id the role's trust policy must require, which is what prevents "
            "another Snowflake account from assuming it."
        ),
    )
    azure_tenant_id: PropertyRef = PropertyRef(
        "azure_tenant_id",
        description="Entra ID tenant the integration requests an access token from.",
    )
    azure_ad_application_id: PropertyRef = PropertyRef(
        "azure_ad_application_id",
        extra_index=True,
        description="Application id of the Entra ID app registration fronting the API.",
    )
    google_audience: PropertyRef = PropertyRef(
        "google_audience",
        description="Audience claim Snowflake requests in its Google-signed token.",
    )
    allowed_authentication_secrets: PropertyRef = PropertyRef(
        "allowed_authentication_secrets",
        description="Secrets a Git repository integration may authenticate with.",
    )
    allowed_api_authentication_integrations: PropertyRef = PropertyRef(
        "allowed_api_authentication_integrations",
        description="Security integrations that may supply OAuth tokens for the API calls.",
    )
    comment: PropertyRef = PropertyRef(
        "comment", description="API integration comment."
    )
    created_on: PropertyRef = PropertyRef(
        "created_on", description="When the API integration was created."
    )


@dataclass(frozen=True)
class SnowflakeApiIntegrationToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeAccount)-[:RESOURCE]->(:SnowflakeApiIntegration)
class SnowflakeApiIntegrationToAccountRel(CartographyRelSchema):
    """A Snowflake account contains the API integration as a resource."""

    target_node_label: str = "SnowflakeAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SnowflakeApiIntegrationToAccountRelProperties = (
        SnowflakeApiIntegrationToAccountRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeApiIntegrationToAWSPrincipalRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeApiIntegration)-[:ASSUMES_ROLE]->(:AWSPrincipal)
class SnowflakeApiIntegrationToAWSPrincipalRel(CartographyRelSchema):
    """A Snowflake API integration assumes an AWS IAM role to invoke its endpoint."""

    target_node_label: str = "AWSPrincipal"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("api_aws_role_arn")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ASSUMES_ROLE"
    properties: SnowflakeApiIntegrationToAWSPrincipalRelProperties = (
        SnowflakeApiIntegrationToAWSPrincipalRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeApiIntegrationSchema(CartographyNodeSchema):
    """Represents a Snowflake API integration: the outbound HTTPS proxy configuration used by external functions and Git repositories."""

    label: str = "SnowflakeApiIntegration"
    properties: SnowflakeApiIntegrationNodeProperties = (
        SnowflakeApiIntegrationNodeProperties()
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([SNOWFLAKE_SECURABLE])
    sub_resource_relationship: SnowflakeApiIntegrationToAccountRel = (
        SnowflakeApiIntegrationToAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [SnowflakeApiIntegrationToAWSPrincipalRel()],
    )
