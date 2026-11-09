from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_source_node_matcher
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import SourceNodeMatcher
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
class DatabricksMetastoreAssignmentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label", set_in_kwargs=True
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)
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
# A MatchLink scoped to the workspace, so each workspace prunes only its own
# assignment and never another workspace's assignment to the same metastore.
class DatabricksMetastoreAssignmentRel(CartographyRelSchema):
    """A Databricks workspace is assigned to a metastore."""

    source_node_label: str = "DatabricksWorkspace"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("WORKSPACE_ID", set_in_kwargs=True)},
    )
    target_node_label: str = "DatabricksMetastore"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ASSIGNED_METASTORE"
    properties: DatabricksMetastoreAssignmentRelProperties = (
        DatabricksMetastoreAssignmentRelProperties()
    )


@dataclass(frozen=True)
class DatabricksMetastoreSchema(CartographyNodeSchema):
    """A Unity Catalog metastore that governs data and access controls.

    The metastore is the root of every Unity Catalog object and is shared by all
    workspaces assigned to it, so it has no parent of its own and is never
    pruned automatically; its objects are scoped to it for cleanup.
    """

    label: str = "DatabricksMetastore"
    properties: DatabricksMetastoreNodeProperties = DatabricksMetastoreNodeProperties()
    # Metastores are grantable UC securables (metastore-level admin privileges).
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([DATABRICKS_SECURABLE])
