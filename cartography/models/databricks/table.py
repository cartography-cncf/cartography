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
class DatabricksTableNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Metastore-scoped identifier for the table."
    )
    table_id: PropertyRef = PropertyRef(
        "table_id", extra_index=True, description="Databricks identifier for the table."
    )
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Name of the table."
    )
    full_name: PropertyRef = PropertyRef(
        "full_name",
        extra_index=True,
        description="Full catalog, schema, and table name.",
    )
    catalog_name: PropertyRef = PropertyRef(
        "catalog_name",
        extra_index=True,
        description="Name of the catalog that contains the table.",
    )
    schema_name: PropertyRef = PropertyRef(
        "schema_name",
        extra_index=True,
        description="Name of the schema that contains the table.",
    )
    metastore_id: PropertyRef = PropertyRef(
        "metastore_id",
        extra_index=True,
        description="Identifier of the metastore that contains the table.",
    )
    table_type: PropertyRef = PropertyRef(
        "table_type", description="Type of the table or view."
    )
    data_source_format: PropertyRef = PropertyRef(
        "data_source_format", description="Data source format used by the table."
    )
    owner: PropertyRef = PropertyRef(
        "owner", extra_index=True, description="Principal that owns the table."
    )
    comment: PropertyRef = PropertyRef(
        "comment", description="User-provided description of the table."
    )
    storage_location: PropertyRef = PropertyRef(
        "storage_location", description="Cloud storage location of the table data."
    )
    view_definition: PropertyRef = PropertyRef(
        "view_definition", description="SQL definition of the view."
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="Timestamp when the table was created."
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at", description="Timestamp when the table was last updated."
    )
    created_by: PropertyRef = PropertyRef(
        "created_by", description="Principal that created the table."
    )
    updated_by: PropertyRef = PropertyRef(
        "updated_by", description="Principal that last updated the table."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DatabricksTableToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksWorkspace)-[:RESOURCE]->(:DatabricksTable)
class DatabricksTableToWorkspaceRel(CartographyRelSchema):
    """A Databricks table is a resource within a workspace."""

    target_node_label: str = "DatabricksWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WORKSPACE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DatabricksTableToWorkspaceRelProperties = (
        DatabricksTableToWorkspaceRelProperties()
    )


@dataclass(frozen=True)
class DatabricksTableToSchemaRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksSchema)-[:CONTAINS]->(:DatabricksTable)
class DatabricksTableToSchemaRel(CartographyRelSchema):
    """A Databricks schema contains a table."""

    target_node_label: str = "DatabricksSchema"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("parent_schema_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: DatabricksTableToSchemaRelProperties = (
        DatabricksTableToSchemaRelProperties()
    )


@dataclass(frozen=True)
class DatabricksTableToS3RelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksTable)-[:BACKED_BY]->(:AWSS3Bucket)
class DatabricksTableToS3Rel(CartographyRelSchema):
    """A Databricks table is backed by an Amazon S3 bucket."""

    target_node_label: str = "AWSS3Bucket"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"name": PropertyRef("s3_bucket")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "BACKED_BY"
    properties: DatabricksTableToS3RelProperties = DatabricksTableToS3RelProperties()


@dataclass(frozen=True)
class DatabricksTableToGCSRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksTable)-[:BACKED_BY]->(:GCPBucket)
class DatabricksTableToGCSRel(CartographyRelSchema):
    """A Databricks table is backed by a Google Cloud Storage bucket."""

    target_node_label: str = "GCPBucket"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("gcs_bucket")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "BACKED_BY"
    properties: DatabricksTableToGCSRelProperties = DatabricksTableToGCSRelProperties()


@dataclass(frozen=True)
class DatabricksTableSchema(CartographyNodeSchema):
    """A Unity Catalog table or view."""

    label: str = "DatabricksTable"
    properties: DatabricksTableNodeProperties = DatabricksTableNodeProperties()
    # DatabricksSecurable: shared UC-grant target label. Database: ontology
    # label for cross-provider data store queries.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        [DATABRICKS_SECURABLE, DATABASE]
    )
    sub_resource_relationship: DatabricksTableToWorkspaceRel = (
        DatabricksTableToWorkspaceRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            DatabricksTableToSchemaRel(),
            DatabricksTableToS3Rel(),
            DatabricksTableToGCSRel(),
        ],
    )
