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
from cartography.models.ontology.labels import DATABASE


@dataclass(frozen=True)
class DatabricksCatalogNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Metastore-scoped identifier for the catalog.",
    )
    catalog_id: PropertyRef = PropertyRef(
        "catalog_id",
        extra_index=True,
        description="Databricks identifier for the catalog.",
    )
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Name of the catalog."
    )
    full_name: PropertyRef = PropertyRef(
        "full_name", extra_index=True, description="Full name of the catalog."
    )
    metastore_id: PropertyRef = PropertyRef(
        "metastore_id",
        extra_index=True,
        description="Identifier of the metastore that contains the catalog.",
    )
    catalog_type: PropertyRef = PropertyRef(
        "catalog_type", description="Type of the catalog."
    )
    owner: PropertyRef = PropertyRef(
        "owner", extra_index=True, description="Principal that owns the catalog."
    )
    comment: PropertyRef = PropertyRef(
        "comment", description="User-provided description of the catalog."
    )
    isolation_mode: PropertyRef = PropertyRef(
        "isolation_mode", description="Workspace isolation mode of the catalog."
    )
    storage_root: PropertyRef = PropertyRef(
        "storage_root", description="Cloud storage root for managed catalog data."
    )
    connection_name: PropertyRef = PropertyRef(
        "connection_name",
        extra_index=True,
        description="Name of the connection used by a foreign catalog.",
    )
    share_name: PropertyRef = PropertyRef(
        "share_name", description="Name of the share that provides the catalog."
    )
    provider_name: PropertyRef = PropertyRef(
        "provider_name", description="Name of the provider for a shared catalog."
    )
    securable_kind: PropertyRef = PropertyRef(
        "securable_kind", description="Unity Catalog securable kind of the catalog."
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="Timestamp when the catalog was created."
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at", description="Timestamp when the catalog was last updated."
    )
    created_by: PropertyRef = PropertyRef(
        "created_by", description="Principal that created the catalog."
    )
    updated_by: PropertyRef = PropertyRef(
        "updated_by", description="Principal that last updated the catalog."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DatabricksCatalogToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksWorkspace)-[:RESOURCE]->(:DatabricksCatalog)
class DatabricksCatalogToWorkspaceRel(CartographyRelSchema):
    """A Databricks catalog is a resource within a workspace."""

    target_node_label: str = "DatabricksWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WORKSPACE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DatabricksCatalogToWorkspaceRelProperties = (
        DatabricksCatalogToWorkspaceRelProperties()
    )


@dataclass(frozen=True)
class DatabricksCatalogToMetastoreRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksMetastore)-[:CONTAINS]->(:DatabricksCatalog)
class DatabricksCatalogToMetastoreRel(CartographyRelSchema):
    """A Databricks metastore contains a catalog."""

    target_node_label: str = "DatabricksMetastore"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("metastore_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: DatabricksCatalogToMetastoreRelProperties = (
        DatabricksCatalogToMetastoreRelProperties()
    )


@dataclass(frozen=True)
class DatabricksCatalogSchema(CartographyNodeSchema):
    """A Unity Catalog catalog that organizes data and other securables."""

    label: str = "DatabricksCatalog"
    properties: DatabricksCatalogNodeProperties = DatabricksCatalogNodeProperties()
    # DatabricksSecurable: shared label so UC grants can target any grantable
    # securable by one label. Database: ontology label for cross-provider data
    # store queries.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        [DATABRICKS_SECURABLE, DATABASE]
    )
    sub_resource_relationship: DatabricksCatalogToWorkspaceRel = (
        DatabricksCatalogToWorkspaceRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [DatabricksCatalogToMetastoreRel()],
    )
