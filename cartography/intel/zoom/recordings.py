from typing import Any
from urllib.parse import quote

import neo4j

from cartography.client.core.tx import load
from cartography.graph.statement import GraphStatement
from cartography.intel.zoom.client import ZoomClient
from cartography.intel.zoom.util import date_windows
from cartography.intel.zoom.util import fetch_many
from cartography.intel.zoom.util import optional_call
from cartography.intel.zoom.util import parse_datetime
from cartography.models.zoom.recording import ZoomRecordingSchema
from cartography.util import timeit


def settings_path(uuid: str) -> str:
    # Zoom requires a second encoding for UUIDs starting with / or containing //.
    encoded = quote(uuid, safe="")
    if uuid.startswith("/") or "//" in uuid:
        encoded = quote(encoded, safe="")
    return f"/meetings/{encoded}/recordings/settings"


def get(client: ZoomClient, host_id: str, lookback_days: int) -> list[dict[str, Any]]:
    recordings: dict[str, dict[str, Any]] = {}
    for window in date_windows(lookback_days):
        for recording in client.get_paginated(
            f"/users/{quote(host_id, safe='')}/recordings",
            "meetings",
            params={**window, "recording_source_type": "cloud_recording_only"},
        ):
            recordings[recording["uuid"]] = recording
    settings = fetch_many(client, [settings_path(uuid) for uuid in recordings])
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


def cleanup(
    neo4j_session: neo4j.Session, account_id: str, host_id: str, update_tag: int
) -> None:
    # A tenant-wide GraphJob would delete snapshots belonging to denied hosts.
    GraphStatement(
        """
        MATCH (n:ZoomRecording {account_id: $account_id, host_id: $host_id})
        WHERE n.lastupdated <> $update_tag
        WITH n LIMIT $LIMIT_SIZE
        DETACH DELETE n
        """,
        parameters={
            "account_id": account_id,
            "host_id": host_id,
            "update_tag": update_tag,
        },
        iterative=True,
        iterationsize=1000,
        parent_job_name="ZoomRecording",
    ).run(neo4j_session)
    GraphStatement(
        """
        MATCH (n:ZoomRecording {account_id: $account_id, host_id: $host_id})-[r:HOSTED_BY|RECORDED_FROM]->()
        WHERE r.lastupdated <> $update_tag
        WITH r LIMIT $LIMIT_SIZE
        DELETE r
        """,
        parameters={
            "account_id": account_id,
            "host_id": host_id,
            "update_tag": update_tag,
        },
        iterative=True,
        iterationsize=1000,
        parent_job_name="ZoomRecording",
    ).run(neo4j_session)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: ZoomClient,
    account_id: str,
    update_tag: int,
    users: list[dict[str, Any]],
    lookback_days: int = 7,
) -> None:
    for user in users:
        if not user.get("zoom_id") or user["status"] != "active" or user["type"] != 2:
            continue
        host_id = user["zoom_id"]
        raw = optional_call("recordings", lambda: get(client, host_id, lookback_days))
        if raw is None:
            continue
        data = transform(raw, account_id)
        load(
            neo4j_session,
            ZoomRecordingSchema(),
            data,
            ACCOUNT_ID=account_id,
            lastupdated=update_tag,
        )
        cleanup(neo4j_session, account_id, host_id, update_tag)
    GraphStatement(
        """
        MATCH (n:ZoomRecording {account_id: $account_id})
        WHERE NOT n.host_id IN $host_ids
        WITH n LIMIT $LIMIT_SIZE
        DETACH DELETE n
        """,
        parameters={
            "account_id": account_id,
            "host_ids": [user["zoom_id"] for user in users if user.get("zoom_id")],
        },
        iterative=True,
        iterationsize=1000,
        parent_job_name="ZoomRecording",
    ).run(neo4j_session)
