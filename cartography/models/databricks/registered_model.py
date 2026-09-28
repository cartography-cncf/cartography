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
class DatabricksRegisteredModelNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Metastore-scoped identifier for the registered model."
    )
    model_id: PropertyRef = PropertyRef(
        "model_id",
        extra_index=True,
        description="Databricks identifier for the registered model.",
    )
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Name of the registered model."
    )
    full_name: PropertyRef = PropertyRef(
        "full_name",
        extra_index=True,
        description="Full catalog, schema, and registered model name.",
    )
    catalog_name: PropertyRef = PropertyRef(
        "catalog_name",
        extra_index=True,
        description="Name of the catalog that contains the registered model.",
    )
    schema_name: PropertyRef = PropertyRef(
        "schema_name",
        extra_index=True,
        description="Name of the schema that contains the registered model.",
    )
    metastore_id: PropertyRef = PropertyRef(
        "metastore_id",
        extra_index=True,
        description="Identifier of the metastore that contains the registered model.",
    )
    owner: PropertyRef = PropertyRef(
        "owner",
        extra_index=True,
        description="Principal that owns the registered model.",
    )
    comment: PropertyRef = PropertyRef(
        "comment", description="User-provided description of the registered model."
    )
    storage_location: PropertyRef = PropertyRef(
        "storage_location",
        description="Cloud storage location for the registered model.",
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="Timestamp when the registered model was created."
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at",
        description="Timestamp when the registered model was last updated.",
    )
    created_by: PropertyRef = PropertyRef(
        "created_by", description="Principal that created the registered model."
    )
    updated_by: PropertyRef = PropertyRef(
        "updated_by",
        description="Principal that last updated the registered model.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DatabricksRegisteredModelToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksWorkspace)-[:RESOURCE]->(:DatabricksRegisteredModel)
class DatabricksRegisteredModelToWorkspaceRel(CartographyRelSchema):
    """A Databricks registered model is a resource within a workspace."""

    target_node_label: str = "DatabricksWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WORKSPACE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DatabricksRegisteredModelToWorkspaceRelProperties = (
        DatabricksRegisteredModelToWorkspaceRelProperties()
    )


@dataclass(frozen=True)
class DatabricksRegisteredModelToSchemaRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksSchema)-[:CONTAINS]->(:DatabricksRegisteredModel)
class DatabricksRegisteredModelToSchemaRel(CartographyRelSchema):
    """A Databricks schema contains a registered model."""

    target_node_label: str = "DatabricksSchema"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("parent_schema_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: DatabricksRegisteredModelToSchemaRelProperties = (
        DatabricksRegisteredModelToSchemaRelProperties()
    )


@dataclass(frozen=True)
class DatabricksRegisteredModelSchema(CartographyNodeSchema):
    """A machine learning model registered in Unity Catalog."""

    label: str = "DatabricksRegisteredModel"
    properties: DatabricksRegisteredModelNodeProperties = (
        DatabricksRegisteredModelNodeProperties()
    )
    # Registered models are grantable UC securables.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([DATABRICKS_SECURABLE])
    sub_resource_relationship: DatabricksRegisteredModelToWorkspaceRel = (
        DatabricksRegisteredModelToWorkspaceRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [DatabricksRegisteredModelToSchemaRel()],
    )


@dataclass(frozen=True)
class DatabricksModelVersionNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Identifier for the registered model version."
    )
    version: PropertyRef = PropertyRef(
        "version", description="Version number within the registered model."
    )
    model_name: PropertyRef = PropertyRef(
        "model_name",
        extra_index=True,
        description="Name of the registered model.",
    )
    metastore_id: PropertyRef = PropertyRef(
        "metastore_id",
        extra_index=True,
        description="Identifier of the metastore that contains the model version.",
    )
    status: PropertyRef = PropertyRef(
        "status", description="Lifecycle status of the model version."
    )
    source: PropertyRef = PropertyRef(
        "source", description="Source URI from which the model version was created."
    )
    run_id: PropertyRef = PropertyRef(
        "run_id",
        extra_index=True,
        description="Identifier of the MLflow run that produced the model version.",
    )
    storage_location: PropertyRef = PropertyRef(
        "storage_location", description="Cloud storage location of the model version."
    )
    comment: PropertyRef = PropertyRef(
        "comment", description="User-provided description of the model version."
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="Timestamp when the model version was created."
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at", description="Timestamp when the model version was last updated."
    )
    created_by: PropertyRef = PropertyRef(
        "created_by", description="Principal that created the model version."
    )
    updated_by: PropertyRef = PropertyRef(
        "updated_by", description="Principal that last updated the model version."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DatabricksModelVersionToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksWorkspace)-[:RESOURCE]->(:DatabricksModelVersion)
class DatabricksModelVersionToWorkspaceRel(CartographyRelSchema):
    """A Databricks model version is a resource within a workspace."""

    target_node_label: str = "DatabricksWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WORKSPACE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DatabricksModelVersionToWorkspaceRelProperties = (
        DatabricksModelVersionToWorkspaceRelProperties()
    )


@dataclass(frozen=True)
class DatabricksModelVersionToModelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksRegisteredModel)-[:HAS_VERSION]->(:DatabricksModelVersion)
class DatabricksModelVersionToModelRel(CartographyRelSchema):
    """A Databricks registered model has a model version."""

    target_node_label: str = "DatabricksRegisteredModel"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("model_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_VERSION"
    properties: DatabricksModelVersionToModelRelProperties = (
        DatabricksModelVersionToModelRelProperties()
    )


@dataclass(frozen=True)
class DatabricksModelVersionSchema(CartographyNodeSchema):
    """A version of a machine learning model registered in Unity Catalog."""

    label: str = "DatabricksModelVersion"
    properties: DatabricksModelVersionNodeProperties = (
        DatabricksModelVersionNodeProperties()
    )
    sub_resource_relationship: DatabricksModelVersionToWorkspaceRel = (
        DatabricksModelVersionToWorkspaceRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [DatabricksModelVersionToModelRel()],
    )
