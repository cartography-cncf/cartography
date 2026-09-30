import logging
from typing import Any
from urllib.parse import quote

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.intel.zoom.client import ZoomClient
from cartography.intel.zoom.util import cleanup_hosted
from cartography.intel.zoom.util import fetch_many
from cartography.intel.zoom.util import is_zoom_error
from cartography.intel.zoom.util import optional_call
from cartography.intel.zoom.util import parse_datetime
from cartography.models.zoom.meeting import ZoomMeetingSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


def list_meeting_ids(client: ZoomClient, host_id: str) -> list[int] | None:
    """Return a host's scheduled meeting IDs, or None if the host was not read."""
    try:
        meetings = client.get_paginated(
            f"/users/{quote(host_id, safe='')}/meetings",
            "meetings",
            params={"type": "scheduled"},
        )
    except requests.HTTPError as exc:
        # Documented when the user left after the user inventory was read.
        if is_zoom_error(exc, 404, 1001):
            logger.warning("Zoom meeting host no longer exists; preserving its data")
            return None
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
) -> tuple[list[dict[str, Any]], list[str]]:
    """Return meeting details and the hosts whose inventories were completely read."""
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
    denied = {
        meeting_id
        for meeting_id, detail in zip(meeting_ids, details, strict=True)
        if detail is None
    }
    readable = [
        host_id
        for host_id, ids in zip(host_ids, listed, strict=True)
        if ids is not None and denied.isdisjoint(ids)
    ]
    return [detail for detail in details if detail], readable


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
    # Pending users and users without a Basic/Licensed seat are not read; their
    # meetings keep the prior snapshot until they are read or leave the account.
    host_ids = [
        user["zoom_id"]
        for user in users
        if user.get("zoom_id")
        and user["status"] != "pending"
        and user["type"] in (1, 2)
    ]
    unavailable: set[str] = set()
    meetings, readable = get(client, host_ids, unavailable)
    load(
        neo4j_session,
        ZoomMeetingSchema(),
        transform(meetings, account_id),
        ACCOUNT_ID=account_id,
        lastupdated=update_tag,
    )
    if len(readable) < len(host_ids):
        logger.warning(
            "Zoom meetings: %d of %d eligible hosts were not completely read; preserving their prior meetings.",
            len(host_ids) - len(readable),
            len(host_ids),
        )
    cleanup_hosted(
        neo4j_session,
        "ZoomMeeting",
        account_id,
        update_tag,
        readable,
        [user["zoom_id"] for user in users if user.get("zoom_id")],
    )
