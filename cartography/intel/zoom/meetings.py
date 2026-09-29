from typing import Any
from urllib.parse import quote

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.zoom.client import ZoomClient
from cartography.intel.zoom.util import fetch_many
from cartography.intel.zoom.util import optional_call
from cartography.intel.zoom.util import parse_datetime
from cartography.models.zoom.meeting import ZoomMeetingSchema
from cartography.util import timeit


def get(client: ZoomClient, host_id: str) -> list[dict[str, Any]]:
    meetings = client.get_paginated(
        f"/users/{quote(host_id, safe='')}/meetings",
        "meetings",
        params={"type": "scheduled"},
    )
    paths = list(dict.fromkeys(f"/meetings/{int(item['id'])}" for item in meetings))
    return fetch_many(client, paths)


def transform(meetings: list[dict[str, Any]], account_id: str) -> list[dict[str, Any]]:
    result = []
    for meeting in meetings:
        settings = meeting["settings"]
        meeting_id = str(meeting["id"])
        host_id = meeting["host_id"]
        result.append(
            {
                "id": f"{account_id}:meeting:{meeting_id}",
                "meeting_id": meeting_id,
                "host_id": host_id,
                "host_graph_id": f"{account_id}:user:{host_id}",
                "topic": meeting.get("topic"),
                "type": meeting.get("type"),
                "status": meeting.get("status"),
                "start_time": parse_datetime(meeting.get("start_time")),
                "created_at": parse_datetime(meeting.get("created_at")),
                "duration": meeting.get("duration"),
                "password_protected": (
                    bool(meeting["password"]) if "password" in meeting else None
                ),
                "waiting_room": settings.get("waiting_room"),
                "meeting_authentication": settings.get("meeting_authentication"),
                "authentication_domains": settings.get("authentication_domains"),
                "join_before_host": settings.get("join_before_host"),
                "approval_type": settings.get("approval_type"),
                "encryption_type": settings.get("encryption_type"),
                "auto_recording": settings.get("auto_recording"),
            }
        )
    return result


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: ZoomClient,
    account_id: str,
    update_tag: int,
    users: list[dict[str, Any]],
) -> None:
    preserved_hosts = []
    unavailable: set[str] = set()
    for user in users:
        if not user.get("zoom_id"):
            continue
        host_id = user["zoom_id"]
        if user["status"] == "pending" or user["type"] not in (1, 2):
            preserved_hosts.append(host_id)
            continue
        raw = optional_call("meetings", lambda: get(client, host_id), unavailable)
        if raw is None:
            preserved_hosts.append(host_id)
            continue
        data = transform(raw, account_id)
        load(
            neo4j_session,
            ZoomMeetingSchema(),
            data,
            ACCOUNT_ID=account_id,
            lastupdated=update_tag,
        )
    # Finish all healthy hosts before pruning, preserving identity on host transfers.
    GraphJob.from_node_schema(
        ZoomMeetingSchema(),
        {"ACCOUNT_ID": account_id, "UPDATE_TAG": update_tag},
        iterationsize=1000,
        excluded_node_filters={"host_id": preserved_hosts},
    ).run(neo4j_session)
    # Complete user inventory is authoritative even for same-tag orphan snapshots.
    GraphJob.from_node_schema(
        ZoomMeetingSchema(),
        {"ACCOUNT_ID": account_id, "UPDATE_TAG": update_tag},
        iterationsize=1000,
        excluded_node_filters={
            "host_id": [user["zoom_id"] for user in users if user.get("zoom_id")],
        },
        delete_current=True,
    ).run(neo4j_session)
