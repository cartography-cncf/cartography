from typing import Any

import neo4j

from cartography.client.core.tx import load_matchlinks
from cartography.graph.job import GraphJob
from cartography.models.databricks.unity_catalog import (
    DatabricksSecurableVisibleInWorkspaceRel,
)
from cartography.models.databricks.unity_catalog import (
    LegacyUnityCatalogWorkspaceResourceCleanupSchema,
)

# Labels that hung off the workspace with RESOURCE before Unity Catalog objects
# were scoped to their metastore.
_LEGACY_WORKSPACE_SCOPED_LABELS = (
    "DatabricksMetastore",
    "DatabricksCatalog",
    "DatabricksSchema",
    "DatabricksTable",
    "DatabricksVolume",
    "DatabricksFunction",
    "DatabricksRegisteredModel",
    "DatabricksModelVersion",
    "DatabricksConnection",
    "DatabricksShare",
    "DatabricksRecipient",
    "DatabricksProvider",
    "DatabricksCleanRoom",
    "DatabricksArtifactAllowlist",
    "DatabricksStorageCredential",
    "DatabricksExternalLocation",
    "DatabricksOnlineTable",
)


def load_visibility(
    neo4j_session: neo4j.Session,
    securables: list[dict[str, Any]],
    workspace_id: str,
    update_tag: int,
) -> None:
    """Link each securable this workspace listed to the workspace (VISIBLE_IN)."""
    if not securables:
        return
    load_matchlinks(
        neo4j_session,
        DatabricksSecurableVisibleInWorkspaceRel(),
        [{"id": s["id"]} for s in securables],
        lastupdated=update_tag,
        WORKSPACE_ID=workspace_id,
        _sub_resource_label="DatabricksWorkspace",
        _sub_resource_id=workspace_id,
    )


def cleanup_visibility(
    neo4j_session: neo4j.Session, workspace_id: str, update_tag: int
) -> None:
    GraphJob.from_matchlink(
        DatabricksSecurableVisibleInWorkspaceRel(),
        "DatabricksWorkspace",
        workspace_id,
        update_tag,
    ).run(neo4j_session)


# DEPRECATED: cleanup of pre-metastore-scope workspace RESOURCE edges will be
# removed in v1.0.0.
def cleanup_legacy_workspace_resource_edges(
    neo4j_session: neo4j.Session, workspace_id: str, update_tag: int
) -> None:
    for label in _LEGACY_WORKSPACE_SCOPED_LABELS:
        GraphJob.from_node_schema(
            LegacyUnityCatalogWorkspaceResourceCleanupSchema(label=label),
            {"UPDATE_TAG": update_tag, "WORKSPACE_ID": workspace_id},
        ).run(neo4j_session)
