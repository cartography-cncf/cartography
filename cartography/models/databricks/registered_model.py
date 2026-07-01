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
class DatabricksRegisteredModelNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    model_id: PropertyRef = PropertyRef("model_id", extra_index=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    full_name: PropertyRef = PropertyRef("full_name", extra_index=True)
    catalog_name: PropertyRef = PropertyRef("catalog_name", extra_index=True)
    schema_name: PropertyRef = PropertyRef("schema_name", extra_index=True)
    metastore_id: PropertyRef = PropertyRef("metastore_id", extra_index=True)
    owner: PropertyRef = PropertyRef("owner", extra_index=True)
    comment: PropertyRef = PropertyRef("comment")
    storage_location: PropertyRef = PropertyRef("storage_location")
    created_at: PropertyRef = PropertyRef("created_at")
    updated_at: PropertyRef = PropertyRef("updated_at")
    created_by: PropertyRef = PropertyRef("created_by")
    updated_by: PropertyRef = PropertyRef("updated_by")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DatabricksRegisteredModelToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksWorkspace)-[:RESOURCE]->(:DatabricksRegisteredModel)
class DatabricksRegisteredModelToWorkspaceRel(CartographyRelSchema):
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
    label: str = "DatabricksRegisteredModel"
    properties: DatabricksRegisteredModelNodeProperties = (
        DatabricksRegisteredModelNodeProperties()
    )
    # Registered models are grantable UC securables.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["DatabricksSecurable"])
    sub_resource_relationship: DatabricksRegisteredModelToWorkspaceRel = (
        DatabricksRegisteredModelToWorkspaceRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [DatabricksRegisteredModelToSchemaRel()],
    )


@dataclass(frozen=True)
class DatabricksModelVersionNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    version: PropertyRef = PropertyRef("version")
    model_name: PropertyRef = PropertyRef("model_name", extra_index=True)
    metastore_id: PropertyRef = PropertyRef("metastore_id", extra_index=True)
    status: PropertyRef = PropertyRef("status")
    source: PropertyRef = PropertyRef("source")
    run_id: PropertyRef = PropertyRef("run_id", extra_index=True)
    storage_location: PropertyRef = PropertyRef("storage_location")
    comment: PropertyRef = PropertyRef("comment")
    created_at: PropertyRef = PropertyRef("created_at")
    updated_at: PropertyRef = PropertyRef("updated_at")
    created_by: PropertyRef = PropertyRef("created_by")
    updated_by: PropertyRef = PropertyRef("updated_by")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DatabricksModelVersionToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksWorkspace)-[:RESOURCE]->(:DatabricksModelVersion)
class DatabricksModelVersionToWorkspaceRel(CartographyRelSchema):
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
