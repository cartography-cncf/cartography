from dataclasses import dataclass
from typing import ClassVar

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_source_node_matcher
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import SourceNodeMatcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class DatabricksSecurableVisibleInWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label", set_in_kwargs=True
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksSecurable)-[:VISIBLE_IN]->(:DatabricksWorkspace)
# Unity Catalog objects belong to the metastore, but what each workspace can list
# differs (catalog bindings, permissions). A MatchLink scoped to the workspace
# records that, so a workspace losing sight of an object prunes only its own
# edge while the object survives for the workspaces that still list it.
class DatabricksSecurableVisibleInWorkspaceRel(CartographyRelSchema):
    """A Unity Catalog securable was listed by this workspace's sync."""

    source_node_label: str = "DatabricksWorkspace"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("WORKSPACE_ID", set_in_kwargs=True)},
    )
    target_node_label: str = "DatabricksSecurable"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "VISIBLE_IN"
    properties: DatabricksSecurableVisibleInWorkspaceRelProperties = (
        DatabricksSecurableVisibleInWorkspaceRelProperties()
    )


# DEPRECATED: cleanup of the workspace RESOURCE edges Unity Catalog objects had
# before they were scoped to their metastore will be removed in v1.0.0.
@dataclass(frozen=True)
class LegacyUnityCatalogNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class LegacyUnityCatalogToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class LegacyUnityCatalogToWorkspaceRel(CartographyRelSchema):
    __cartography_introspection_exclude__: ClassVar[bool] = True

    target_node_label: str = "DatabricksWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WORKSPACE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: LegacyUnityCatalogToWorkspaceRelProperties = (
        LegacyUnityCatalogToWorkspaceRelProperties()
    )


@dataclass(frozen=True)
class LegacyUnityCatalogWorkspaceResourceCleanupSchema(CartographyNodeSchema):
    """Cleanup-only template, specialised per Unity Catalog label.

    Without a sub-resource, cleanup deletes only stale relationships, never
    nodes. Nothing writes a workspace RESOURCE edge to these labels any more, so
    every such edge is stale and goes on the first cleanup after an upgrade.
    """

    __cartography_introspection_exclude__: ClassVar[bool] = True

    label: str = "DatabricksCatalog"
    properties: LegacyUnityCatalogNodeProperties = LegacyUnityCatalogNodeProperties()
    other_relationships: OtherRelationships = OtherRelationships(
        [LegacyUnityCatalogToWorkspaceRel()],
    )
