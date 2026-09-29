import logging
from typing import Any
from urllib.parse import quote

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.zoom.client import ZoomClient
from cartography.intel.zoom.util import date_windows
from cartography.intel.zoom.util import encode_uuid
from cartography.intel.zoom.util import fetch_many
from cartography.intel.zoom.util import optional_call
from cartography.intel.zoom.util import parse_datetime
from cartography.models.zoom.recording import ZoomRecordingSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


def settings_path(uuid: str) -> str:
    return f"/meetings/{encode_uuid(uuid)}/recordings/settings"


def get(
    client: ZoomClient, host_id: str, lookback_days: int
) -> list[dict[str, Any]] | None:
    recordings: dict[str, dict[str, Any]] = {}
    for window in date_windows(lookback_days):
        for recording in client.get_paginated(
            f"/users/{quote(host_id, safe='')}/recordings",
            "meetings",
            params={**window, "recording_source_type": "cloud_recording_only"},
        ):
            recordings[recording["uuid"]] = recording
    try:
        settings = fetch_many(client, [settings_path(uuid) for uuid in recordings])
    except requests.HTTPError as exc:
        response = exc.response
        if response is None or response.status_code != 404:
            raise
        try:
            code = response.json().get("code")
        except requests.exceptions.JSONDecodeError:
            raise exc
        if code != 3301:
            raise
        logger.warning(
            "Zoom recording is still processing (HTTP 404, code 3301); preserving this host's prior recording snapshot."
        )
        return None
    return [
        {**recording, "settings": setting}
        for recording, setting in zip(recordings.values(), settings, strict=True)
    ]


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
    readable_owners = []
    unavailable: set[str] = set()
    for user in users:
        # Ineligible or unreadable owners keep their prior snapshot.
        if not user.get("zoom_id") or user["status"] != "active" or user["type"] != 2:
            continue
        host_id = user["zoom_id"]
        raw = optional_call(
            "recordings", lambda: get(client, host_id, lookback_days), unavailable
        )
        if raw is None:
            continue
        load(
            neo4j_session,
            ZoomRecordingSchema(),
            transform(raw, account_id),
            ACCOUNT_ID=account_id,
            OWNER_ID=user["id"],
            lastupdated=update_tag,
        )
        readable_owners.append(user["id"])
    # Finish all readable owners before pruning, preserving identity on host
    # transfers. Removed users' snapshots are deleted with the user.
    for owner_id in readable_owners:
        GraphJob.from_node_schema(
            ZoomRecordingSchema(),
            {"OWNER_ID": owner_id, "UPDATE_TAG": update_tag},
            iterationsize=1000,
        ).run(neo4j_session)
