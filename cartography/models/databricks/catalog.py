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
class DatabricksCatalogNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    catalog_id: PropertyRef = PropertyRef("catalog_id", extra_index=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    full_name: PropertyRef = PropertyRef("full_name", extra_index=True)
    metastore_id: PropertyRef = PropertyRef("metastore_id", extra_index=True)
    catalog_type: PropertyRef = PropertyRef("catalog_type")
    owner: PropertyRef = PropertyRef("owner", extra_index=True)
    comment: PropertyRef = PropertyRef("comment")
    isolation_mode: PropertyRef = PropertyRef("isolation_mode")
    storage_root: PropertyRef = PropertyRef("storage_root")
    connection_name: PropertyRef = PropertyRef("connection_name", extra_index=True)
    share_name: PropertyRef = PropertyRef("share_name")
    provider_name: PropertyRef = PropertyRef("provider_name")
    securable_kind: PropertyRef = PropertyRef("securable_kind")
    created_at: PropertyRef = PropertyRef("created_at")
    updated_at: PropertyRef = PropertyRef("updated_at")
    created_by: PropertyRef = PropertyRef("created_by")
    updated_by: PropertyRef = PropertyRef("updated_by")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DatabricksCatalogToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksWorkspace)-[:RESOURCE]->(:DatabricksCatalog)
class DatabricksCatalogToWorkspaceRel(CartographyRelSchema):
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
    label: str = "DatabricksCatalog"
    properties: DatabricksCatalogNodeProperties = DatabricksCatalogNodeProperties()
    # DatabricksSecurable: shared label so UC grants can target any grantable
    # securable by one label. Database: ontology label for cross-provider data
    # store queries.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        ["DatabricksSecurable", "Database"]
    )
    sub_resource_relationship: DatabricksCatalogToWorkspaceRel = (
        DatabricksCatalogToWorkspaceRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [DatabricksCatalogToMetastoreRel()],
    )
