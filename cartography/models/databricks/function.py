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
class DatabricksFunctionNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    function_id: PropertyRef = PropertyRef("function_id", extra_index=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    full_name: PropertyRef = PropertyRef("full_name", extra_index=True)
    catalog_name: PropertyRef = PropertyRef("catalog_name", extra_index=True)
    schema_name: PropertyRef = PropertyRef("schema_name", extra_index=True)
    metastore_id: PropertyRef = PropertyRef("metastore_id", extra_index=True)
    data_type: PropertyRef = PropertyRef("data_type")
    routine_body: PropertyRef = PropertyRef("routine_body")
    external_language: PropertyRef = PropertyRef("external_language")
    security_type: PropertyRef = PropertyRef("security_type")
    sql_data_access: PropertyRef = PropertyRef("sql_data_access")
    is_deterministic: PropertyRef = PropertyRef("is_deterministic")
    owner: PropertyRef = PropertyRef("owner", extra_index=True)
    comment: PropertyRef = PropertyRef("comment")
    created_at: PropertyRef = PropertyRef("created_at")
    updated_at: PropertyRef = PropertyRef("updated_at")
    created_by: PropertyRef = PropertyRef("created_by")
    updated_by: PropertyRef = PropertyRef("updated_by")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DatabricksFunctionToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksWorkspace)-[:RESOURCE]->(:DatabricksFunction)
class DatabricksFunctionToWorkspaceRel(CartographyRelSchema):
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
    label: str = "DatabricksFunction"
    properties: DatabricksFunctionNodeProperties = DatabricksFunctionNodeProperties()
    # Shared label so UC grants can target any grantable securable by one label.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["DatabricksSecurable"])
    sub_resource_relationship: DatabricksFunctionToWorkspaceRel = (
        DatabricksFunctionToWorkspaceRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [DatabricksFunctionToSchemaRel()],
    )
