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
from cartography.models.ontology.labels import DATABASE


@dataclass(frozen=True)
class DatabricksSchemaNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Metastore-scoped identifier for the schema.",
    )
    schema_id: PropertyRef = PropertyRef(
        "schema_id",
        extra_index=True,
        description="Databricks identifier for the schema.",
    )
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Name of the schema."
    )
    full_name: PropertyRef = PropertyRef(
        "full_name",
        extra_index=True,
        description="Full catalog and schema name.",
    )
    catalog_name: PropertyRef = PropertyRef(
        "catalog_name",
        extra_index=True,
        description="Name of the catalog that contains the schema.",
    )
    metastore_id: PropertyRef = PropertyRef(
        "metastore_id",
        extra_index=True,
        description="Identifier of the metastore that contains the schema.",
    )
    owner: PropertyRef = PropertyRef(
        "owner", extra_index=True, description="Principal that owns the schema."
    )
    comment: PropertyRef = PropertyRef(
        "comment", description="User-provided description of the schema."
    )
    storage_root: PropertyRef = PropertyRef(
        "storage_root", description="Cloud storage root for managed schema data."
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="Timestamp when the schema was created."
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at", description="Timestamp when the schema was last updated."
    )
    created_by: PropertyRef = PropertyRef(
        "created_by", description="Principal that created the schema."
    )
    updated_by: PropertyRef = PropertyRef(
        "updated_by", description="Principal that last updated the schema."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DatabricksSchemaToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksWorkspace)-[:RESOURCE]->(:DatabricksSchema)
class DatabricksSchemaToWorkspaceRel(CartographyRelSchema):
    """A Databricks schema is a resource within a workspace."""

    target_node_label: str = "DatabricksWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WORKSPACE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DatabricksSchemaToWorkspaceRelProperties = (
        DatabricksSchemaToWorkspaceRelProperties()
    )


@dataclass(frozen=True)
class DatabricksSchemaToCatalogRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksCatalog)-[:CONTAINS]->(:DatabricksSchema)
class DatabricksSchemaToCatalogRel(CartographyRelSchema):
    """A Databricks catalog contains a schema."""

    target_node_label: str = "DatabricksCatalog"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("catalog_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: DatabricksSchemaToCatalogRelProperties = (
        DatabricksSchemaToCatalogRelProperties()
    )


@dataclass(frozen=True)
class DatabricksSchemaSchema(CartographyNodeSchema):
    """A Unity Catalog schema that organizes data objects within a catalog."""

    label: str = "DatabricksSchema"
    properties: DatabricksSchemaNodeProperties = DatabricksSchemaNodeProperties()
    # DatabricksSecurable: shared UC-grant target label. Database: ontology
    # label for cross-provider data store queries.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        [DATABRICKS_SECURABLE, DATABASE]
    )
    sub_resource_relationship: DatabricksSchemaToWorkspaceRel = (
        DatabricksSchemaToWorkspaceRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [DatabricksSchemaToCatalogRel()],
    )
