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
from cartography.intel.zoom.util import optional_call
from cartography.intel.zoom.util import parse_datetime
from cartography.models.zoom.meeting import ZoomMeetingSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


def list_meeting_ids(client: ZoomClient, host_id: str) -> list[int] | None:
    """Return a host's scheduled meeting IDs, or None if the read was denied."""
    try:
        meetings = client.get_paginated(
            f"/users/{quote(host_id, safe='')}/meetings",
            "meetings",
            params={"type": "scheduled"},
        )
    except requests.HTTPError as exc:
        # Documented when the user left after the user inventory was read: the
        # host has no meetings to load.
        if is_zoom_error(exc, 404, 1001):
            logger.warning("Zoom meeting host no longer exists; skipping its meetings")
            return []
        raise
    return list(dict.fromkeys(int(item["id"]) for item in meetings))


def get_meeting(client: ZoomClient, meeting_id: int) -> dict[str, Any]:
    """Return meeting details; an empty result means Zoom reports it deleted."""
    try:
        return client.get(f"/meetings/{meeting_id}")
    except requests.HTTPError as exc:
        # Documented for a meeting deleted after its host's list was read.
        if is_zoom_error(exc, 404, 3001):
            return {}
        raise


@timeit
def get(
    client: ZoomClient, host_ids: list[str], unavailable: set[str]
) -> tuple[list[dict[str, Any]], bool]:
    """Return meeting details and whether every host and meeting was read."""
    listed = fetch_many(
        client,
        host_ids,
        lambda worker, host_id: optional_call(
            "meetings", lambda: list_meeting_ids(worker, host_id), unavailable
        ),
    )
    meeting_ids = list(
        dict.fromkeys(
            meeting_id for ids in listed if ids is not None for meeting_id in ids
        )
    )
    details = fetch_many(
        client,
        meeting_ids,
        lambda worker, meeting_id: optional_call(
            "meetings", lambda: get_meeting(worker, meeting_id), unavailable
        ),
    )
    complete = all(ids is not None for ids in listed) and all(
        detail is not None for detail in details
    )
    return [detail for detail in details if detail], complete


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
    # Pending users and users without a Basic/Licensed seat cannot host meetings.
    host_ids = [
        user["zoom_id"]
        for user in users
        if user.get("zoom_id")
        and user["status"] != "pending"
        and user["type"] in (1, 2)
    ]
    unavailable: set[str] = set()
    meetings, complete = get(client, host_ids, unavailable)
    load(
        neo4j_session,
        ZoomMeetingSchema(),
        transform(meetings, account_id),
        ACCOUNT_ID=account_id,
        lastupdated=update_tag,
    )
    if not complete:
        logger.warning(
            "Zoom meetings were not completely read; skipping cleanup so prior meetings are kept."
        )
        return
    GraphJob.from_node_schema(
        ZoomMeetingSchema(),
        {"UPDATE_TAG": update_tag, "ACCOUNT_ID": account_id},
    ).run(neo4j_session)
