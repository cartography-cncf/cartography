from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.models.notion.workspace import NotionWorkspaceSchema


def transform(workspace_id: str, workspace_name: str) -> list[dict[str, Any]]:
    return [{"id": workspace_id, "name": workspace_name}]


def sync(
    neo4j_session: neo4j.Session,
    workspace_id: str,
    workspace_name: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        NotionWorkspaceSchema(),
        transform(workspace_id, workspace_name),
        lastupdated=update_tag,
    )
