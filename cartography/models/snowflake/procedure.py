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
class SnowflakeProcedureNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Account-scoped identifier for the stored procedure."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Procedure name, without its arguments."
    )
    qualified_name: PropertyRef = PropertyRef(
        "qualified_name",
        description=(
            "Fully-qualified database.schema.procedure name with its normalised "
            "argument list, which is what makes an overloaded procedure unique."
        ),
    )
    database_name: PropertyRef = PropertyRef(
        "database_name", description="Database containing the procedure."
    )
    schema_name: PropertyRef = PropertyRef(
        "schema_name", description="Schema containing the procedure."
    )
    signature: PropertyRef = PropertyRef(
        "signature",
        description="Normalised argument type list distinguishing this overload.",
    )
    returns: PropertyRef = PropertyRef(
        "returns", description="Data type the procedure returns."
    )
    language: PropertyRef = PropertyRef(
        "language",
        description="Language the handler is written in, such as SQL, PYTHON or JAVA.",
    )
    execute_as: PropertyRef = PropertyRef(
        "execute_as",
        description=(
            "Whether the body runs with the privileges of the procedure owner "
            "(OWNER) or of the role that called it (CALLER). An owner-rights "
            "procedure lends its owner's privileges to anyone allowed to call it."
        ),
    )
    is_secure: PropertyRef = PropertyRef(
        "is_secure",
        description="Whether Snowflake hides the procedure's definition from non-owners.",
    )
    is_external_function: PropertyRef = PropertyRef(
        "is_external_function",
        description="Whether the procedure calls out to a remote HTTPS service.",
    )
    is_memoizable: PropertyRef = PropertyRef(
        "is_memoizable",
        description="Whether Snowflake may cache the procedure's result per session.",
    )
    is_builtin: PropertyRef = PropertyRef(
        "is_builtin",
        description="Whether the procedure ships with Snowflake rather than being user-defined.",
    )
    api_integration: PropertyRef = PropertyRef(
        "api_integration",
        description="API integration the procedure calls a remote service through.",
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
        "owner", description="Name of the role that owns the procedure."
    )
    comment: PropertyRef = PropertyRef("comment", description="Procedure comment.")
    created_on: PropertyRef = PropertyRef(
        "created_on", description="When the procedure was created."
    )


@dataclass(frozen=True)
class SnowflakeProcedureToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeAccount)-[:RESOURCE]->(:SnowflakeProcedure)
class SnowflakeProcedureToAccountRel(CartographyRelSchema):
    """A Snowflake account contains the stored procedure as a resource."""

    target_node_label: str = "SnowflakeAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SnowflakeProcedureToAccountRelProperties = (
        SnowflakeProcedureToAccountRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeProcedureToSchemaRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeSchema)-[:CONTAINS]->(:SnowflakeProcedure)
class SnowflakeProcedureToSchemaRel(CartographyRelSchema):
    """A Snowflake schema holds the stored procedure in its namespace."""

    target_node_label: str = "SnowflakeSchema"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("parent_schema_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: SnowflakeProcedureToSchemaRelProperties = (
        SnowflakeProcedureToSchemaRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeProcedureToOwnerRoleRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeProcedure)-[:ASSUMES]->(:SnowflakeRole)
class SnowflakeProcedureToOwnerRoleRel(CartographyRelSchema):
    """An owner-rights stored procedure executes with the privileges of its owning role.

    This is the Snowflake equivalent of a privilege-escalation stepping stone: any
    role that may call the procedure gets the owner's privileges for the duration
    of the body. Absent for a caller-rights procedure, which runs with whatever
    privileges the caller already had.
    """

    target_node_label: str = "SnowflakeRole"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("owner_role_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ASSUMES"
    properties: SnowflakeProcedureToOwnerRoleRelProperties = (
        SnowflakeProcedureToOwnerRoleRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeProcedureToExternalAccessIntegrationRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeProcedure)-[:USES_INTEGRATION]->(:SnowflakeExternalAccessIntegration)
class SnowflakeProcedureToExternalAccessIntegrationRel(CartographyRelSchema):
    """A Snowflake stored procedure reaches the network through this external access integration."""

    target_node_label: str = "SnowflakeExternalAccessIntegration"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("external_access_integration_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES_INTEGRATION"
    properties: SnowflakeProcedureToExternalAccessIntegrationRelProperties = (
        SnowflakeProcedureToExternalAccessIntegrationRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeProcedureToSecretRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeProcedure)-[:USES_SECRET]->(:SnowflakeSecret)
class SnowflakeProcedureToSecretRel(CartographyRelSchema):
    """A Snowflake stored procedure is allowed to read this secret at runtime."""

    target_node_label: str = "SnowflakeSecret"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("secret_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES_SECRET"
    properties: SnowflakeProcedureToSecretRelProperties = (
        SnowflakeProcedureToSecretRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeProcedureSchema(CartographyNodeSchema):
    """Represents a Snowflake stored procedure: a callable body of code that can run with its owner's privileges.

    A procedure name alone does not identify a procedure, because the same name
    can be overloaded with different argument types in one schema, so the
    identifier carries a normalised argument list as well. Known limitation: SHOW
    GRANTS renders a procedure's arguments differently from the object API, so a
    privilege granted on a specific overload may not attach to this node.
    """

    label: str = "SnowflakeProcedure"
    properties: SnowflakeProcedureNodeProperties = SnowflakeProcedureNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        [FUNCTION, SNOWFLAKE_SECURABLE],
    )
    sub_resource_relationship: SnowflakeProcedureToAccountRel = (
        SnowflakeProcedureToAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            SnowflakeProcedureToSchemaRel(),
            SnowflakeProcedureToOwnerRoleRel(),
            SnowflakeProcedureToExternalAccessIntegrationRel(),
            SnowflakeProcedureToSecretRel(),
        ],
    )
