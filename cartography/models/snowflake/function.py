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
from cartography.models.ontology.labels import FUNCTION
from cartography.models.snowflake.extra_labels import SNOWFLAKE_SECURABLE


@dataclass(frozen=True)
class SnowflakeFunctionNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Account-scoped identifier for the function."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Function name, without its arguments."
    )
    qualified_name: PropertyRef = PropertyRef(
        "qualified_name",
        description=(
            "Fully-qualified database.schema.function name with its normalised "
            "argument list, which is what makes an overloaded function unique."
        ),
    )
    database_name: PropertyRef = PropertyRef(
        "database_name", description="Database containing the function."
    )
    schema_name: PropertyRef = PropertyRef(
        "schema_name", description="Schema containing the function."
    )
    signature: PropertyRef = PropertyRef(
        "signature",
        description="Normalised argument type list distinguishing this overload.",
    )
    returns: PropertyRef = PropertyRef(
        "returns", description="Data type the function returns."
    )
    language: PropertyRef = PropertyRef(
        "language",
        description="Language the handler is written in, such as SQL, PYTHON or JAVA.",
    )
    is_secure: PropertyRef = PropertyRef(
        "is_secure",
        description=(
            "Whether the function is secure, meaning Snowflake hides its definition "
            "and keeps the optimizer from leaking underlying data."
        ),
    )
    is_external_function: PropertyRef = PropertyRef(
        "is_external_function",
        description=(
            "Whether the function calls out to a remote HTTPS service, which sends "
            "query data outside Snowflake."
        ),
    )
    is_memoizable: PropertyRef = PropertyRef(
        "is_memoizable",
        description="Whether Snowflake may cache the function's result per session.",
    )
    is_builtin: PropertyRef = PropertyRef(
        "is_builtin",
        description="Whether the function ships with Snowflake rather than being user-defined.",
    )
    api_integration: PropertyRef = PropertyRef(
        "api_integration",
        description="API integration an external function calls its remote service through.",
    )
    handler: PropertyRef = PropertyRef(
        "handler", description="Entry point Snowflake invokes inside the code."
    )
    runtime_version: PropertyRef = PropertyRef(
        "runtime_version", description="Language runtime version the handler runs on."
    )
    packages: PropertyRef = PropertyRef(
        "packages", description="Third-party packages the handler imports."
    )
    imports: PropertyRef = PropertyRef(
        "imports", description="Staged files the handler loads its code from."
    )
    external_access_integrations: PropertyRef = PropertyRef(
        "external_access_integrations",
        description="External access integrations that let the handler reach the network.",
    )
    secrets: PropertyRef = PropertyRef(
        "secrets",
        description="References to the Snowflake secrets the handler is allowed to read.",
    )
    owner: PropertyRef = PropertyRef(
        "owner", description="Name of the role that owns the function."
    )
    comment: PropertyRef = PropertyRef("comment", description="Function comment.")
    created_on: PropertyRef = PropertyRef(
        "created_on", description="When the function was created."
    )


@dataclass(frozen=True)
class SnowflakeFunctionToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeAccount)-[:RESOURCE]->(:SnowflakeFunction)
class SnowflakeFunctionToAccountRel(CartographyRelSchema):
    """A Snowflake account contains the function as a resource."""

    target_node_label: str = "SnowflakeAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SnowflakeFunctionToAccountRelProperties = (
        SnowflakeFunctionToAccountRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeFunctionToSchemaRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeSchema)-[:CONTAINS]->(:SnowflakeFunction)
class SnowflakeFunctionToSchemaRel(CartographyRelSchema):
    """A Snowflake schema holds the function in its namespace."""

    target_node_label: str = "SnowflakeSchema"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("parent_schema_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: SnowflakeFunctionToSchemaRelProperties = (
        SnowflakeFunctionToSchemaRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeFunctionToExternalAccessIntegrationRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeFunction)-[:USES_INTEGRATION]->(:SnowflakeExternalAccessIntegration)
class SnowflakeFunctionToExternalAccessIntegrationRel(CartographyRelSchema):
    """A Snowflake function reaches the network through this external access integration.

    The integration is what turns a sandboxed handler into one that can talk to
    the outside world, so it marks a function as a potential egress path.
    """

    target_node_label: str = "SnowflakeExternalAccessIntegration"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("external_access_integration_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES_INTEGRATION"
    properties: SnowflakeFunctionToExternalAccessIntegrationRelProperties = (
        SnowflakeFunctionToExternalAccessIntegrationRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeFunctionToSecretRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeFunction)-[:USES_SECRET]->(:SnowflakeSecret)
class SnowflakeFunctionToSecretRel(CartographyRelSchema):
    """A Snowflake function is allowed to read this secret at runtime."""

    target_node_label: str = "SnowflakeSecret"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("secret_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES_SECRET"
    properties: SnowflakeFunctionToSecretRelProperties = (
        SnowflakeFunctionToSecretRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeFunctionToApiIntegrationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeFunction)-[:USES_INTEGRATION]->(:SnowflakeApiIntegration)
class SnowflakeFunctionToApiIntegrationRel(CartographyRelSchema):
    """An external Snowflake function calls its remote service through this API integration."""

    target_node_label: str = "SnowflakeApiIntegration"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("api_integration_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES_INTEGRATION"
    properties: SnowflakeFunctionToApiIntegrationRelProperties = (
        SnowflakeFunctionToApiIntegrationRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeFunctionSchema(CartographyNodeSchema):
    """Represents a Snowflake user-defined function: code that runs inside the account whenever a query calls it.

    A function name alone does not identify a function, because the same name can
    be overloaded with different argument types in one schema, so the identifier
    carries a normalised argument list as well. Known limitation: SHOW GRANTS
    renders a function's arguments differently from the object API, so a privilege
    granted on a specific overload may not attach to this node.
    """

    label: str = "SnowflakeFunction"
    properties: SnowflakeFunctionNodeProperties = SnowflakeFunctionNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        [FUNCTION, SNOWFLAKE_SECURABLE],
    )
    sub_resource_relationship: SnowflakeFunctionToAccountRel = (
        SnowflakeFunctionToAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            SnowflakeFunctionToSchemaRel(),
            SnowflakeFunctionToExternalAccessIntegrationRel(),
            SnowflakeFunctionToSecretRel(),
            SnowflakeFunctionToApiIntegrationRel(),
        ],
    )
