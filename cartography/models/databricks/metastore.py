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


@dataclass(frozen=True)
class DatabricksMetastoreNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Cartography graph identifier for the metastore."
    )
    metastore_id: PropertyRef = PropertyRef(
        "metastore_id",
        extra_index=True,
        description="Native Databricks identifier for the metastore.",
    )
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Name of the metastore."
    )
    global_metastore_id: PropertyRef = PropertyRef(
        "global_metastore_id",
        extra_index=True,
        description="Globally unique identifier for the metastore.",
    )
    cloud: PropertyRef = PropertyRef(
        "cloud", description="Cloud provider that hosts the metastore."
    )
    region: PropertyRef = PropertyRef(
        "region", description="Cloud region of the metastore."
    )
    delta_sharing_scope: PropertyRef = PropertyRef(
        "delta_sharing_scope", description="Sharing scope configured for the metastore."
    )
    external_access_enabled: PropertyRef = PropertyRef(
        "external_access_enabled",
        description="Whether external Delta Sharing is enabled.",
    )
    privilege_model_version: PropertyRef = PropertyRef(
        "privilege_model_version",
        description="Version of the Unity Catalog privilege model.",
    )
    owner: PropertyRef = PropertyRef(
        "owner", extra_index=True, description="Principal that owns the metastore."
    )
    storage_root: PropertyRef = PropertyRef(
        "storage_root", description="Cloud storage root for managed metastore data."
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="Timestamp when the metastore was created."
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at", description="Timestamp when the metastore was last updated."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DatabricksMetastoreToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksWorkspace)-[:RESOURCE]->(:DatabricksMetastore)
# Sub-resource edge so metastore cleanup is scoped per workspace, matching the
# single-workspace ingestion model used across the module.
class DatabricksMetastoreToWorkspaceRel(CartographyRelSchema):
    """A Databricks metastore is a resource within a workspace."""

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
    default_catalog_name: PropertyRef = PropertyRef(
        "default_catalog_name",
        description="Name of the workspace's default catalog.",
    )
    workspace_numeric_id: PropertyRef = PropertyRef(
        "workspace_numeric_id",
        description="Numeric Databricks identifier for the assigned workspace.",
    )


@dataclass(frozen=True)
# (:DatabricksWorkspace)-[:ASSIGNED_METASTORE]->(:DatabricksMetastore)
# The semantic assignment edge, carrying the workspace's default catalog.
class DatabricksMetastoreAssignmentRel(CartographyRelSchema):
    """A Databricks workspace is assigned to a metastore."""

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
    """A Unity Catalog metastore that governs data and access controls."""

    label: str = "DatabricksMetastore"
    properties: DatabricksMetastoreNodeProperties = DatabricksMetastoreNodeProperties()
    # Metastores are grantable UC securables (metastore-level admin privileges).
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([DATABRICKS_SECURABLE])
    sub_resource_relationship: DatabricksMetastoreToWorkspaceRel = (
        DatabricksMetastoreToWorkspaceRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [DatabricksMetastoreAssignmentRel()],
    )
