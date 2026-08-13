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
from cartography.models.ontology.labels import SECRET
from cartography.models.snowflake.extra_labels import SNOWFLAKE_SECURABLE


@dataclass(frozen=True)
class SnowflakeSecretNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Account-scoped identifier for the secret."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="The secret name."
    )
    qualified_name: PropertyRef = PropertyRef(
        "qualified_name",
        extra_index=True,
        description="Fully qualified DATABASE.SCHEMA.NAME of the secret.",
    )
    database_name: PropertyRef = PropertyRef(
        "database_name", description="Name of the database containing the secret."
    )
    schema_name: PropertyRef = PropertyRef(
        "schema_name", description="Name of the schema containing the secret."
    )
    secret_type: PropertyRef = PropertyRef(
        "secret_type",
        description=(
            "Kind of credential held: PASSWORD, OAUTH2, GENERIC_STRING, "
            "SYMMETRIC_KEY or a private-key type."
        ),
    )
    username: PropertyRef = PropertyRef(
        "username",
        description="Username half of a PASSWORD secret. The password itself is never stored.",
    )
    oauth_scopes: PropertyRef = PropertyRef(
        "oauth_scopes",
        description="OAuth scopes the secret's token is issued for.",
    )
    oauth_refresh_token_expiry_time: PropertyRef = PropertyRef(
        "oauth_refresh_token_expiry_time",
        description=(
            "When the stored OAuth refresh token expires. A past value means calls using "
            "the secret already fail."
        ),
    )
    api_authentication: PropertyRef = PropertyRef(
        "api_authentication",
        description="Name of the security integration that issues the secret's OAuth token.",
    )
    algorithm: PropertyRef = PropertyRef(
        "algorithm", description="Algorithm of a symmetric-key secret."
    )
    key_length: PropertyRef = PropertyRef(
        "key_length", description="Length in bits of a symmetric-key secret."
    )
    owner: PropertyRef = PropertyRef(
        "owner", description="Name of the role that owns the secret."
    )
    comment: PropertyRef = PropertyRef("comment", description="Secret comment.")
    created_on: PropertyRef = PropertyRef(
        "created_on", description="When the secret was created."
    )


@dataclass(frozen=True)
class SnowflakeSecretToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeAccount)-[:RESOURCE]->(:SnowflakeSecret)
class SnowflakeSecretToAccountRel(CartographyRelSchema):
    """A Snowflake account contains the secret as a resource."""

    target_node_label: str = "SnowflakeAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SnowflakeSecretToAccountRelProperties = (
        SnowflakeSecretToAccountRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeSecretToSchemaRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeSchema)-[:CONTAINS]->(:SnowflakeSecret)
class SnowflakeSecretToSchemaRel(CartographyRelSchema):
    """A Snowflake schema contains the secret."""

    target_node_label: str = "SnowflakeSchema"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("parent_schema_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: SnowflakeSecretToSchemaRelProperties = (
        SnowflakeSecretToSchemaRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeSecretToSecurityIntegrationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeSecret)-[:USES_INTEGRATION]->(:SnowflakeSecurityIntegration)
class SnowflakeSecretToSecurityIntegrationRel(CartographyRelSchema):
    """A Snowflake secret obtains its OAuth token from this security integration."""

    target_node_label: str = "SnowflakeSecurityIntegration"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("api_authentication_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES_INTEGRATION"
    properties: SnowflakeSecretToSecurityIntegrationRelProperties = (
        SnowflakeSecretToSecurityIntegrationRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeSecretSchema(CartographyNodeSchema):
    """Represents a Snowflake secret: a schema-level credential used by external access and API calls."""

    label: str = "SnowflakeSecret"
    properties: SnowflakeSecretNodeProperties = SnowflakeSecretNodeProperties()
    # Secret: ontology label; a Snowflake secret holds a credential.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        [SECRET, SNOWFLAKE_SECURABLE],
    )
    sub_resource_relationship: SnowflakeSecretToAccountRel = (
        SnowflakeSecretToAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            SnowflakeSecretToSchemaRel(),
            SnowflakeSecretToSecurityIntegrationRel(),
        ],
    )
