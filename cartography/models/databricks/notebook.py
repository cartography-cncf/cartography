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
class DatabricksNotebookNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    path: PropertyRef = PropertyRef("path", extra_index=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DatabricksNotebookToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksWorkspace)-[:RESOURCE]->(:DatabricksNotebook)
class DatabricksNotebookToWorkspaceRel(CartographyRelSchema):
    target_node_label: str = "DatabricksWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WORKSPACE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DatabricksNotebookToWorkspaceRelProperties = (
        DatabricksNotebookToWorkspaceRelProperties()
    )


@dataclass(frozen=True)
class DatabricksNotebookToJobTaskRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksJobTask)-[:RUNS_NOTEBOOK]->(:DatabricksNotebook)
# Matches job tasks by the workspace-scoped notebook id (task.notebook_scoped_id
# == notebook.id), not the raw path, so two workspaces sharing a notebook path
# cannot produce a cross-workspace edge. The notebook is a lightweight,
# path-keyed node (no content / permissions) derived only from the workloads
# that reference it, so there is no full workspace walk.
class DatabricksNotebookToJobTaskRel(CartographyRelSchema):
    target_node_label: str = "DatabricksJobTask"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"notebook_scoped_id": PropertyRef("id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RUNS_NOTEBOOK"
    properties: DatabricksNotebookToJobTaskRelProperties = (
        DatabricksNotebookToJobTaskRelProperties()
    )


@dataclass(frozen=True)
class DatabricksNotebookSchema(CartographyNodeSchema):
    label: str = "DatabricksNotebook"
    properties: DatabricksNotebookNodeProperties = DatabricksNotebookNodeProperties()
    sub_resource_relationship: DatabricksNotebookToWorkspaceRel = (
        DatabricksNotebookToWorkspaceRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [DatabricksNotebookToJobTaskRel()],
    )
