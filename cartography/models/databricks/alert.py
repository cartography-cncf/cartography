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
class DatabricksAlertNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    alert_id: PropertyRef = PropertyRef("alert_id", extra_index=True)
    display_name: PropertyRef = PropertyRef("display_name", extra_index=True)
    query_id: PropertyRef = PropertyRef("query_id", extra_index=True)
    owner_user_name: PropertyRef = PropertyRef("owner_user_name", extra_index=True)
    state: PropertyRef = PropertyRef("state")
    lifecycle_state: PropertyRef = PropertyRef("lifecycle_state")
    condition_op: PropertyRef = PropertyRef("condition_op")
    parent_path: PropertyRef = PropertyRef("parent_path")
    create_time: PropertyRef = PropertyRef("create_time")
    update_time: PropertyRef = PropertyRef("update_time")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DatabricksAlertToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksWorkspace)-[:RESOURCE]->(:DatabricksAlert)
class DatabricksAlertToWorkspaceRel(CartographyRelSchema):
    target_node_label: str = "DatabricksWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WORKSPACE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DatabricksAlertToWorkspaceRelProperties = (
        DatabricksAlertToWorkspaceRelProperties()
    )


@dataclass(frozen=True)
class DatabricksAlertToQueryRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksAlert)-[:MONITORS]->(:DatabricksQuery)
class DatabricksAlertToQueryRel(CartographyRelSchema):
    target_node_label: str = "DatabricksQuery"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("query_scoped_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MONITORS"
    properties: DatabricksAlertToQueryRelProperties = (
        DatabricksAlertToQueryRelProperties()
    )


@dataclass(frozen=True)
class DatabricksAlertSchema(CartographyNodeSchema):
    label: str = "DatabricksAlert"
    properties: DatabricksAlertNodeProperties = DatabricksAlertNodeProperties()
    sub_resource_relationship: DatabricksAlertToWorkspaceRel = (
        DatabricksAlertToWorkspaceRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [DatabricksAlertToQueryRel()],
    )
