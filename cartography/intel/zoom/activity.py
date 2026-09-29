import hashlib
import json
import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.helpers import normalize_email_for_matching
from cartography.intel.zoom.client import ZoomClient
from cartography.intel.zoom.util import date_windows
from cartography.intel.zoom.util import encode_uuid
from cartography.intel.zoom.util import fetch_many
from cartography.intel.zoom.util import is_zoom_error
from cartography.intel.zoom.util import optional_call
from cartography.intel.zoom.util import parse_datetime
from cartography.models.zoom.activity import ZoomMeetingAuditEventSchema
from cartography.models.zoom.activity import ZoomOperationEventSchema
from cartography.models.zoom.activity import ZoomSignInEventSchema
from cartography.models.zoom.client_version import ZoomClientVersionSchema
from cartography.models.zoom.participant import ZoomMeetingParticipantSchema
from cartography.models.zoom.session import ZoomMeetingSessionSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


def fingerprint(data: dict[str, Any]) -> str:
    # Report APIs have no event IDs. Exact duplicate records collapse; details
    # contribute to identity but their potentially sensitive text is not stored.
    return hashlib.sha256(
        json.dumps(data, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def get_report(
    client: ZoomClient, path: str, key: str, days: int
) -> list[dict[str, Any]]:
    return [
        row
        for window in date_windows(days)
        for row in client.get_paginated(path, key, window)
    ]


def transform_events(
    rows: list[dict[str, Any]],
    source: str,
    account_id: str,
    users: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    by_email = {user["email"]: user["id"] for user in users}
    result = []
    for row in rows:
        email = normalize_email_for_matching(
            row.get("email") or row.get("operator_email") or row.get("operator")
        )
        value = row.get("time") or row.get("activity_time")
        # Meeting audit times use yyyy-MM-dd HH:mm:ss:SSS, in UTC.
        if source == "meeting_audit" and value and len(value) > 19 and value[19] == ":":
            value = value[:19] + "." + value[20:]
        meeting_id = str(row.get("meeting_number") or "").replace(" ", "")
        result.append(
            {
                "id": f"{account_id}:event:{source}:{fingerprint(row)}",
                "source": source,
                "event_type": row.get("type")
                or row.get("action")
                or row.get("activity_category"),
                "category": row.get("category_type"),
                "occurred_at": parse_datetime(value),
                "operator_email": email,
                "user_node_id": by_email.get(email),
                "client_type": row.get("client_type"),
                "client_version": row.get("version"),
                "meeting_node_id": (
                    f"{account_id}:meeting:{meeting_id}" if meeting_id else None
                ),
            }
        )
    return result


@timeit
def sync_reports(
    session: neo4j.Session,
    client: ZoomClient,
    account_id: str,
    update_tag: int,
    users: list[dict[str, Any]],
    days: int,
) -> None:
    for source, path, key, schema in (
        ("signins", "/report/activities", "activity_logs", ZoomSignInEventSchema()),
        (
            "operations",
            "/report/operationlogs",
            "operation_logs",
            ZoomOperationEventSchema(),
        ),
        (
            "meeting_audit",
            "/report/meeting_activities",
            "meeting_activity_logs",
            ZoomMeetingAuditEventSchema(),
        ),
    ):
        rows = optional_call(source, lambda: get_report(client, path, key, days))
        if rows is None:
            continue
        data = transform_events(rows, source, account_id, users)
        load(session, schema, data, ACCOUNT_ID=account_id, lastupdated=update_tag)
        # Each report is independently authorized; its own label scopes cleanup
        # so denied sources and their edges are preserved.
        GraphJob.from_node_schema(
            schema,
            {"ACCOUNT_ID": account_id, "UPDATE_TAG": update_tag},
            iterationsize=1000,
        ).run(session)


def get_sessions(client: ZoomClient, days: int) -> list[dict[str, Any]]:
    meetings = {}
    for kind in ("past", "pastOne"):
        for window in date_windows(days):
            for meeting in client.get_paginated(
                "/metrics/meetings", "meetings", {**window, "type": kind}
            ):
                meetings[meeting["uuid"]] = {**meeting, "dashboard_type": kind}
    return list(meetings.values())


def get_participants(
    client: ZoomClient, meeting: dict[str, Any]
) -> list[dict[str, Any]] | None:
    """Return participants, or None when Zoom cannot report them yet."""
    try:
        return client.get_paginated(
            f"/metrics/meetings/{encode_uuid(meeting['uuid'])}/participants",
            "participants",
            {"type": meeting["dashboard_type"]},
        )
    except requests.HTTPError as exc:
        # Documented when a listed meeting ID is invalid or has not ended; this
        # is an unread response, not an empty participant list.
        if is_zoom_error(exc, 404, 3001):
            return None
        raise


@timeit
def sync_dashboard(
    session: neo4j.Session,
    client: ZoomClient,
    account_id: str,
    update_tag: int,
    users: list[dict[str, Any]],
    days: int,
) -> None:
    meetings = get_sessions(client, days)
    by_email = {user["email"]: user["id"] for user in users}
    session_data = []
    participants = []
    # Participant reads are Heavy requests; they share the heavy request limit.
    results = fetch_many(client, meetings, get_participants)
    participant_rows = [rows for rows in results if rows is not None]
    if len(participant_rows) < len(meetings):
        logger.warning(
            "Zoom dashboard: %d of %d meetings are invalid or have not ended (HTTP 404, code 3001); preserving the prior dashboard snapshot.",
            len(meetings) - len(participant_rows),
            len(meetings),
        )
        return
    for meeting, rows in zip(meetings, participant_rows, strict=True):
        uuid = meeting["uuid"]
        node_id = f"{account_id}:session:{uuid}"
        session_data.append(
            {
                "id": node_id,
                "uuid": uuid,
                "meeting_id": str(meeting["id"]),
                "meeting_node_id": f"{account_id}:meeting:{meeting['id']}",
                "host_node_id": by_email.get(
                    normalize_email_for_matching(meeting.get("email"))
                ),
                "start_time": parse_datetime(meeting.get("start_time")),
                "end_time": parse_datetime(meeting.get("end_time")),
                "participant_count": meeting.get("participants"),
                "has_recording": meeting.get("has_recording"),
                "has_external_participant": meeting.get("has_external_participant"),
            }
        )
        for participant in rows:
            user_id = participant.get("participant_user_id")
            participants.append(
                {
                    "id": f"{node_id}:participant:{fingerprint({key: participant.get(key) for key in ('user_id', 'participant_user_id', 'join_time')})}",
                    "session_id": node_id,
                    "participant_user_id": user_id,
                    "user_node_id": f"{account_id}:user:{user_id}" if user_id else None,
                    "device": participant.get("device"),
                    "client_version": participant.get("version"),
                    "os": participant.get("os"),
                    "os_version": participant.get("os_version"),
                    "join_time": parse_datetime(participant.get("join_time")),
                    "leave_time": parse_datetime(participant.get("leave_time")),
                    "role": participant.get("role"),
                }
            )
    # Complete dashboard reads precede all writes and cleanup.
    load(
        session,
        ZoomMeetingSessionSchema(),
        session_data,
        ACCOUNT_ID=account_id,
        lastupdated=update_tag,
    )
    load(
        session,
        ZoomMeetingParticipantSchema(),
        participants,
        ACCOUNT_ID=account_id,
        lastupdated=update_tag,
    )
    parameters = {"ACCOUNT_ID": account_id, "UPDATE_TAG": update_tag}
    GraphJob.from_node_schema(ZoomMeetingParticipantSchema(), parameters).run(session)
    GraphJob.from_node_schema(ZoomMeetingSessionSchema(), parameters).run(session)


@timeit
def sync_client_versions(
    session: neo4j.Session, client: ZoomClient, account_id: str, update_tag: int
) -> None:
    versions = client.get("/metrics/client_versions")["client_versions"]
    if not isinstance(versions, list):
        raise ValueError("Zoom client_versions response must contain a list")
    data = {
        f"{account_id}:client_version:{version['client_version']}": {
            "id": f"{account_id}:client_version:{version['client_version']}",
            "client_version": version["client_version"],
            "total_count": version.get("total_count"),
        }
        for version in versions
    }
    load(
        session,
        ZoomClientVersionSchema(),
        list(data.values()),
        ACCOUNT_ID=account_id,
        lastupdated=update_tag,
    )
    GraphJob.from_node_schema(
        ZoomClientVersionSchema(), {"ACCOUNT_ID": account_id, "UPDATE_TAG": update_tag}
    ).run(session)
