import logging
from typing import Any
from urllib.parse import quote

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.intel.zoom.client import ZoomClient
from cartography.intel.zoom.util import cleanup_hosted
from cartography.intel.zoom.util import date_windows
from cartography.intel.zoom.util import encode_uuid
from cartography.intel.zoom.util import fetch_many
from cartography.intel.zoom.util import is_zoom_error
from cartography.intel.zoom.util import optional_call
from cartography.intel.zoom.util import parse_datetime
from cartography.models.zoom.recording import ZoomRecordingSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


def settings_path(uuid: str) -> str:
    return f"/meetings/{encode_uuid(uuid)}/recordings/settings"


def list_recordings(
    client: ZoomClient, host_id: str, lookback_days: int
) -> list[dict[str, Any]] | None:
    """Return a host's cloud recordings in the window, or None if not read."""
    recordings: dict[str, dict[str, Any]] = {}
    try:
        for window in date_windows(lookback_days):
            for recording in client.get_paginated(
                f"/users/{quote(host_id, safe='')}/recordings",
                "meetings",
                params={**window, "recording_source_type": "cloud_recording_only"},
            ):
                recordings[recording["uuid"]] = recording
    except requests.HTTPError as exc:
        # Documented when the user left after the user inventory was read.
        if is_zoom_error(exc, 404, 1001):
            logger.warning("Zoom recording host no longer exists; preserving its data")
            return None
        raise
    return list(recordings.values())


def get_settings(client: ZoomClient, uuid: str) -> dict[str, Any] | None:
    """Return sharing settings, or None while Zoom is still processing the recording."""
    try:
        return client.get(settings_path(uuid))
    except requests.HTTPError as exc:
        if is_zoom_error(exc, 404, 3301):
            logger.warning(
                "Zoom recording is still processing (HTTP 404, code 3301); preserving its host's prior recording snapshot."
            )
            return None
        raise


@timeit
def get(
    client: ZoomClient,
    host_ids: list[str],
    lookback_days: int,
    unavailable: set[str],
) -> tuple[list[dict[str, Any]], list[str]]:
    """Return recordings with settings and the hosts whose inventories were complete."""
    listed = fetch_many(
        client,
        host_ids,
        lambda worker, host_id: optional_call(
            "recordings",
            lambda: list_recordings(worker, host_id, lookback_days),
            unavailable,
        ),
    )
    recordings = {
        recording["uuid"]: recording
        for items in listed
        if items is not None
        for recording in items
    }
    settings = fetch_many(
        client,
        list(recordings),
        lambda worker, uuid: optional_call(
            "recordings", lambda: get_settings(worker, uuid), unavailable
        ),
    )
    unread = {
        uuid
        for uuid, setting in zip(recordings, settings, strict=True)
        if setting is None
    }
    readable = [
        host_id
        for host_id, items in zip(host_ids, listed, strict=True)
        if items is not None and unread.isdisjoint(item["uuid"] for item in items)
    ]
    return [
        {**recording, "settings": setting}
        for recording, setting in zip(recordings.values(), settings, strict=True)
        if setting is not None
    ], readable


def transform(
    recordings: list[dict[str, Any]], account_id: str
) -> list[dict[str, Any]]:
    result = []
    for recording in recordings:
        settings = recording["settings"]
        uuid = recording["uuid"]
        host_id = recording["host_id"]
        meeting_id = str(recording["id"])
        result.append(
            {
                "id": f"{account_id}:recording:{uuid}",
                "meeting_uuid": uuid,
                "meeting_id": meeting_id,
                "meeting_graph_id": f"{account_id}:meeting:{meeting_id}",
                "host_id": host_id,
                "host_graph_id": f"{account_id}:user:{host_id}",
                "topic": recording.get("topic"),
                "start_time": parse_datetime(recording.get("start_time")),
                "duration": recording.get("duration"),
                "total_size": recording.get("total_size"),
                "recording_count": recording.get("recording_count"),
                "file_types": sorted(
                    {file["file_type"] for file in recording.get("recording_files", [])}
                ),
                "password_protected": (
                    bool(settings["password"]) if "password" in settings else None
                ),
                "share_recording": settings.get("share_recording"),
                "recording_authentication": settings.get("recording_authentication"),
                "authentication_domains": settings.get("authentication_domains"),
                "on_demand": settings.get("on_demand"),
                "approval_type": settings.get("approval_type"),
                "viewer_download": settings.get("viewer_download"),
                "auto_delete": settings.get("auto_delete"),
                "auto_delete_date": settings.get("auto_delete_date"),
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
    lookback_days: int = 7,
) -> None:
    # Inactive users and users without a Licensed seat are not read; existing
    # recordings keep the prior snapshot until read or the owner leaves.
    host_ids = [
        user["zoom_id"]
        for user in users
        if user.get("zoom_id") and user["status"] == "active" and user["type"] == 2
    ]
    unavailable: set[str] = set()
    recordings, readable = get(client, host_ids, lookback_days, unavailable)
    load(
        neo4j_session,
        ZoomRecordingSchema(),
        transform(recordings, account_id),
        ACCOUNT_ID=account_id,
        lastupdated=update_tag,
    )
    if len(readable) < len(host_ids):
        logger.warning(
            "Zoom recordings: %d of %d eligible hosts were not completely read; preserving their prior recordings.",
            len(host_ids) - len(readable),
            len(host_ids),
        )
    # Successful hosts also expire recordings that left the rolling window.
    cleanup_hosted(
        neo4j_session,
        "ZoomRecording",
        account_id,
        update_tag,
        readable,
        [user["zoom_id"] for user in users if user.get("zoom_id")],
    )
