import hashlib
import json
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.helpers import normalize_email_for_matching
from cartography.intel.zoom.client import ZoomClient
from cartography.intel.zoom.util import date_windows
from cartography.intel.zoom.util import encode_uuid
from cartography.intel.zoom.util import optional_call
from cartography.intel.zoom.util import parse_datetime
from cartography.models.zoom.activity import ZoomMeetingAuditEventSchema
from cartography.models.zoom.activity import ZoomOperationEventSchema
from cartography.models.zoom.activity import ZoomSignInEventSchema
from cartography.models.zoom.participant import ZoomMeetingParticipantSchema
from cartography.models.zoom.session import ZoomMeetingSessionSchema


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
    for meeting in meetings:
        uuid = meeting["uuid"]
        encoded = encode_uuid(uuid)
        rows = client.get_paginated(
            f"/metrics/meetings/{encoded}/participants",
            "participants",
            {"type": meeting["dashboard_type"]},
        )
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
