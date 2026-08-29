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
from cartography.models.databricks.extra_labels import DATABRICKS_SECURABLE


@dataclass(frozen=True)
class DatabricksFunctionNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Metastore-scoped identifier for the function."
    )
    function_id: PropertyRef = PropertyRef(
        "function_id",
        extra_index=True,
        description="Databricks identifier for the function.",
    )
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Name of the function."
    )
    full_name: PropertyRef = PropertyRef(
        "full_name",
        extra_index=True,
        description="Full catalog, schema, and function name.",
    )
    catalog_name: PropertyRef = PropertyRef(
        "catalog_name",
        extra_index=True,
        description="Name of the catalog that contains the function.",
    )
    schema_name: PropertyRef = PropertyRef(
        "schema_name",
        extra_index=True,
        description="Name of the schema that contains the function.",
    )
    metastore_id: PropertyRef = PropertyRef(
        "metastore_id",
        extra_index=True,
        description="Identifier of the metastore that contains the function.",
    )
    data_type: PropertyRef = PropertyRef(
        "data_type", description="Return data type of the function."
    )
    routine_body: PropertyRef = PropertyRef(
        "routine_body", description="Language used to define the function body."
    )
    external_language: PropertyRef = PropertyRef(
        "external_language", description="Language in which the function is written."
    )
    security_type: PropertyRef = PropertyRef(
        "security_type", description="Security context used to run the function."
    )
    sql_data_access: PropertyRef = PropertyRef(
        "sql_data_access", description="Declared SQL data access behavior."
    )
    is_deterministic: PropertyRef = PropertyRef(
        "is_deterministic",
        description="Whether the function returns the same result for the same inputs.",
    )
    owner: PropertyRef = PropertyRef(
        "owner", extra_index=True, description="Principal that owns the function."
    )
    comment: PropertyRef = PropertyRef(
        "comment", description="User-provided description of the function."
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="Timestamp when the function was created."
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at", description="Timestamp when the function was last updated."
    )
    created_by: PropertyRef = PropertyRef(
        "created_by", description="Principal that created the function."
    )
    updated_by: PropertyRef = PropertyRef(
        "updated_by", description="Principal that last updated the function."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DatabricksFunctionToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksWorkspace)-[:RESOURCE]->(:DatabricksFunction)
class DatabricksFunctionToWorkspaceRel(CartographyRelSchema):
    """A Databricks function is a resource within a workspace."""

    target_node_label: str = "DatabricksWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WORKSPACE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DatabricksFunctionToWorkspaceRelProperties = (
        DatabricksFunctionToWorkspaceRelProperties()
    )


@dataclass(frozen=True)
class DatabricksFunctionToSchemaRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksSchema)-[:CONTAINS]->(:DatabricksFunction)
class DatabricksFunctionToSchemaRel(CartographyRelSchema):
    """A Databricks schema contains a function."""

    target_node_label: str = "DatabricksSchema"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("parent_schema_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: DatabricksFunctionToSchemaRelProperties = (
        DatabricksFunctionToSchemaRelProperties()
    )


@dataclass(frozen=True)
class DatabricksFunctionSchema(CartographyNodeSchema):
    """A user-defined function registered in Unity Catalog."""

    label: str = "DatabricksFunction"
    properties: DatabricksFunctionNodeProperties = DatabricksFunctionNodeProperties()
    # Shared label so UC grants can target any grantable securable by one label.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([DATABRICKS_SECURABLE])
    sub_resource_relationship: DatabricksFunctionToWorkspaceRel = (
        DatabricksFunctionToWorkspaceRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [DatabricksFunctionToSchemaRel()],
    )
