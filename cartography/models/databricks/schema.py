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
class DatabricksSchemaNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    schema_id: PropertyRef = PropertyRef("schema_id", extra_index=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    full_name: PropertyRef = PropertyRef("full_name", extra_index=True)
    catalog_name: PropertyRef = PropertyRef("catalog_name", extra_index=True)
    metastore_id: PropertyRef = PropertyRef("metastore_id", extra_index=True)
    owner: PropertyRef = PropertyRef("owner", extra_index=True)
    comment: PropertyRef = PropertyRef("comment")
    storage_root: PropertyRef = PropertyRef("storage_root")
    created_at: PropertyRef = PropertyRef("created_at")
    updated_at: PropertyRef = PropertyRef("updated_at")
    created_by: PropertyRef = PropertyRef("created_by")
    updated_by: PropertyRef = PropertyRef("updated_by")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DatabricksSchemaToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksWorkspace)-[:RESOURCE]->(:DatabricksSchema)
class DatabricksSchemaToWorkspaceRel(CartographyRelSchema):
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
    label: str = "DatabricksSchema"
    properties: DatabricksSchemaNodeProperties = DatabricksSchemaNodeProperties()
    # DatabricksSecurable: shared UC-grant target label. Database: ontology
    # label for cross-provider data store queries.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        ["DatabricksSecurable", "Database"]
    )
    sub_resource_relationship: DatabricksSchemaToWorkspaceRel = (
        DatabricksSchemaToWorkspaceRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [DatabricksSchemaToCatalogRel()],
    )
