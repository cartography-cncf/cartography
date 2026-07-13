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


@dataclass(frozen=True)
class DatabricksTableNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    table_id: PropertyRef = PropertyRef("table_id", extra_index=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    full_name: PropertyRef = PropertyRef("full_name", extra_index=True)
    catalog_name: PropertyRef = PropertyRef("catalog_name", extra_index=True)
    schema_name: PropertyRef = PropertyRef("schema_name", extra_index=True)
    metastore_id: PropertyRef = PropertyRef("metastore_id", extra_index=True)
    table_type: PropertyRef = PropertyRef("table_type")
    data_source_format: PropertyRef = PropertyRef("data_source_format")
    owner: PropertyRef = PropertyRef("owner", extra_index=True)
    comment: PropertyRef = PropertyRef("comment")
    storage_location: PropertyRef = PropertyRef("storage_location")
    view_definition: PropertyRef = PropertyRef("view_definition")
    created_at: PropertyRef = PropertyRef("created_at")
    updated_at: PropertyRef = PropertyRef("updated_at")
    created_by: PropertyRef = PropertyRef("created_by")
    updated_by: PropertyRef = PropertyRef("updated_by")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DatabricksTableToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksWorkspace)-[:RESOURCE]->(:DatabricksTable)
class DatabricksTableToWorkspaceRel(CartographyRelSchema):
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
# (:DatabricksTable)-[:BACKED_BY]->(:S3Bucket)
class DatabricksTableToS3Rel(CartographyRelSchema):
    target_node_label: str = "S3Bucket"
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
    target_node_label: str = "GCPBucket"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("gcs_bucket")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "BACKED_BY"
    properties: DatabricksTableToGCSRelProperties = DatabricksTableToGCSRelProperties()


@dataclass(frozen=True)
class DatabricksTableSchema(CartographyNodeSchema):
    label: str = "DatabricksTable"
    properties: DatabricksTableNodeProperties = DatabricksTableNodeProperties()
    # DatabricksSecurable: shared UC-grant target label. Database: ontology
    # label for cross-provider data store queries.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        ["DatabricksSecurable", "Database"]
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
