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
class DatabricksMetastoreNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    metastore_id: PropertyRef = PropertyRef("metastore_id", extra_index=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    global_metastore_id: PropertyRef = PropertyRef(
        "global_metastore_id", extra_index=True
    )
    cloud: PropertyRef = PropertyRef("cloud")
    region: PropertyRef = PropertyRef("region")
    delta_sharing_scope: PropertyRef = PropertyRef("delta_sharing_scope")
    external_access_enabled: PropertyRef = PropertyRef("external_access_enabled")
    privilege_model_version: PropertyRef = PropertyRef("privilege_model_version")
    owner: PropertyRef = PropertyRef("owner", extra_index=True)
    storage_root: PropertyRef = PropertyRef("storage_root")
    created_at: PropertyRef = PropertyRef("created_at")
    updated_at: PropertyRef = PropertyRef("updated_at")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DatabricksMetastoreToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksWorkspace)-[:RESOURCE]->(:DatabricksMetastore)
# Sub-resource edge so metastore cleanup is scoped per workspace, matching the
# single-workspace ingestion model used across the module.
class DatabricksMetastoreToWorkspaceRel(CartographyRelSchema):
    target_node_label: str = "DatabricksWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WORKSPACE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DatabricksMetastoreToWorkspaceRelProperties = (
        DatabricksMetastoreToWorkspaceRelProperties()
    )


@dataclass(frozen=True)
class DatabricksMetastoreAssignmentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    default_catalog_name: PropertyRef = PropertyRef("default_catalog_name")
    workspace_numeric_id: PropertyRef = PropertyRef("workspace_numeric_id")


@dataclass(frozen=True)
# (:DatabricksWorkspace)-[:ASSIGNED_METASTORE]->(:DatabricksMetastore)
# The semantic assignment edge, carrying the workspace's default catalog.
class DatabricksMetastoreAssignmentRel(CartographyRelSchema):
    target_node_label: str = "DatabricksWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WORKSPACE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "ASSIGNED_METASTORE"
    properties: DatabricksMetastoreAssignmentRelProperties = (
        DatabricksMetastoreAssignmentRelProperties()
    )


@dataclass(frozen=True)
class DatabricksMetastoreSchema(CartographyNodeSchema):
    label: str = "DatabricksMetastore"
    properties: DatabricksMetastoreNodeProperties = DatabricksMetastoreNodeProperties()
    # Metastores are grantable UC securables (metastore-level admin privileges).
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["DatabricksSecurable"])
    sub_resource_relationship: DatabricksMetastoreToWorkspaceRel = (
        DatabricksMetastoreToWorkspaceRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [DatabricksMetastoreAssignmentRel()],
    )
