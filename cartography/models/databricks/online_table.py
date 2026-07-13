from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class DatabricksOnlineTableNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name", extra_index=True)
    metastore_id: PropertyRef = PropertyRef("metastore_id", extra_index=True)
    source_table_full_name: PropertyRef = PropertyRef(
        "source_table_full_name", extra_index=True
    )
    pipeline_id: PropertyRef = PropertyRef("pipeline_id", extra_index=True)
    detailed_state: PropertyRef = PropertyRef("detailed_state")
    provisioning_state: PropertyRef = PropertyRef("provisioning_state")
    table_serving_url: PropertyRef = PropertyRef("table_serving_url")
    primary_key_columns: PropertyRef = PropertyRef("primary_key_columns")
    timeseries_key: PropertyRef = PropertyRef("timeseries_key")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DatabricksOnlineTableToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksWorkspace)-[:RESOURCE]->(:DatabricksOnlineTable)
class DatabricksOnlineTableToWorkspaceRel(CartographyRelSchema):
    target_node_label: str = "DatabricksWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WORKSPACE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DatabricksOnlineTableToWorkspaceRelProperties = (
        DatabricksOnlineTableToWorkspaceRelProperties()
    )


@dataclass(frozen=True)
class DatabricksOnlineTableToSourceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksOnlineTable)-[:SOURCED_FROM]->(:DatabricksTable)
class DatabricksOnlineTableToSourceRel(CartographyRelSchema):
    target_node_label: str = "DatabricksTable"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("source_table_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "SOURCED_FROM"
    properties: DatabricksOnlineTableToSourceRelProperties = (
        DatabricksOnlineTableToSourceRelProperties()
    )


@dataclass(frozen=True)
class DatabricksOnlineTableSchema(CartographyNodeSchema):
    label: str = "DatabricksOnlineTable"
    properties: DatabricksOnlineTableNodeProperties = (
        DatabricksOnlineTableNodeProperties()
    )
    sub_resource_relationship: DatabricksOnlineTableToWorkspaceRel = (
        DatabricksOnlineTableToWorkspaceRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [DatabricksOnlineTableToSourceRel()],
    )
