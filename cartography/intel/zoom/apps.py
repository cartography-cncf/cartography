import logging
from typing import Any
from urllib.parse import quote

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.zoom.client import ZoomClient
from cartography.intel.zoom.util import fetch_many
from cartography.intel.zoom.util import is_zoom_error
from cartography.models.zoom.app import ZoomAppSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


def get_app(client: ZoomClient, app_id: str) -> dict[str, Any] | None:
    try:
        return client.get(f"/marketplace/apps/{quote(app_id, safe='')}")
    except requests.HTTPError as exc:
        # Documented for an app ID that no longer exists.
        if is_zoom_error(exc, 404, 1401):
            logger.warning("Zoom Marketplace app no longer exists; omitting it")
            return None
        raise


@timeit
def sync(
    session: neo4j.Session, client: ZoomClient, account_id: str, update_tag: int
) -> None:
    apps: dict[str, dict[str, Any]] = {}
    for kind, flag in (("account_added", "installed"), ("approved_apps", "approved")):
        for app in client.get_paginated("/marketplace/apps", "apps", {"type": kind}):
            current = apps.setdefault(
                app["app_id"], {"installed": False, "approved": False}
            )
            current.update(app)
            current[flag] = True
    details = fetch_many(client, list(apps), get_app)
    data = []
    for (app_id, app), detail in zip(apps.items(), details, strict=True):
        if detail is None:
            continue
        approval = app.get("approval_info") or {}
        closed = approval.get("app_approval_closed")
        data.append(
            {
                "id": f"{account_id}:app:{app_id}",
                "app_id": app_id,
                "name": app["app_name"],
                "installed": app["installed"],
                "approved": app["approved"],
                "approval_type": approval.get("approved_type"),
                "approval_required": None if closed is None else not closed,
                "app_status": detail.get("app_status"),
                "app_type": detail.get("app_type"),
                "developer_type": app.get("app_developer_type"),
                "app_scopes": detail.get("app_scopes"),
            }
        )
    load(session, ZoomAppSchema(), data, lastupdated=update_tag, ACCOUNT_ID=account_id)
    GraphJob.from_node_schema(
        ZoomAppSchema(), {"UPDATE_TAG": update_tag, "ACCOUNT_ID": account_id}
    ).run(session)
