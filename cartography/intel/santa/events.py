import logging
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.santa.client import ZentralSantaClient
from cartography.models.santa.application import SantaObservedApplicationSchema
from cartography.models.santa.application_version import (
    SantaObservedApplicationVersionSchema,
)
from cartography.util import timeit

logger = logging.getLogger(__name__)


def _first_value(data: dict[str, Any], field_paths: list[str]) -> str | None:
    for field_path in field_paths:
        current: Any = data
        for part in field_path.split("."):
            if not isinstance(current, dict):
                current = None
                break
            current = current.get(part)

        if isinstance(current, str):
            current = current.strip()
        if current not in (None, ""):
            return str(current)
    return None


def _normalize_identifier(value: str) -> str:
    normalized = value.strip().lower()
    cleaned = []
    for character in normalized:
        if character.isalnum() or character in {":", ".", "-", "_"}:
            cleaned.append(character)
        elif character in {"/", " ", "\\"}:
            cleaned.append("_")
    result = "".join(cleaned).strip("_")
    return result or "unknown"


def _looks_like_email(value: str | None) -> bool:
    return bool(value and "@" in value and "." in value.rsplit("@", maxsplit=1)[-1])


def _extract_machine_id(event: dict[str, Any]) -> str | None:
    return _first_value(
        event,
        [
            "machine.serial_number",
            "machine.serial",
            "machine_serial_number",
            "machine_serial",
            "serial_number",
            "serial",
            "machine_id",
        ],
    )


def _extract_application_identifier(event: dict[str, Any]) -> str | None:
    return _first_value(
        event,
        [
            "target.bundle_identifier",
            "bundle_identifier",
            "bundle_id",
            "file.bundle_identifier",
            "file_bundle_identifier",
            "file.bundle_id",
            "file_bundle_id",
            "file.sha256",
            "file_sha256",
            "sha256",
            "file.path",
            "file_path",
            "path",
            "file_name",
            "filename",
        ],
    )


def _extract_application_name(event: dict[str, Any]) -> str | None:
    path_value = _first_value(event, ["file.path", "file_path", "path"])
    if path_value and "/" in path_value:
        path_value = path_value.rsplit("/", maxsplit=1)[-1]

    return (
        _first_value(
            event,
            [
                "target.display_name",
                "display_name",
                "bundle_name",
                "file.bundle_name",
                "file_name",
                "filename",
            ],
        )
        or path_value
    )


def _extract_application_version(event: dict[str, Any]) -> str:
    return (
        _first_value(
            event,
            [
                "target.version",
                "version",
                "bundle_version",
                "file.bundle_version",
                "app_version",
            ],
        )
        or "unknown"
    )


def _extract_user_id(event: dict[str, Any]) -> str | None:
    user_id = _first_value(
        event,
        [
            "user.id",
            "user.unique_id",
            "principal_user.unique_id",
            "executing_user.id",
            "user_id",
            "principal_user_id",
        ],
    )
    if user_id:
        return user_id

    principal_name = _first_value(
        event,
        [
            "user.principal_name",
            "principal_user.principal_name",
            "executing_user.principal_name",
            "username",
            "user",
        ],
    )
    if principal_name:
        return (
            principal_name.lower()
            if _looks_like_email(principal_name)
            else principal_name
        )

    return None


def _parse_event_timestamp(value: Any) -> datetime | None:
    if value in (None, ""):
        return None

    if isinstance(value, (int, float)):
        timestamp = float(value)
        if timestamp > 10_000_000_000:
            timestamp = timestamp / 1000.0
        return datetime.fromtimestamp(timestamp, tz=timezone.utc)

    if isinstance(value, str):
        raw = value.strip()
        if not raw:
            return None

        if raw.isdigit():
            return _parse_event_timestamp(int(raw))

        if raw.endswith("Z"):
            raw = raw[:-1] + "+00:00"
        try:
            parsed = datetime.fromisoformat(raw)
        except ValueError:
            return None
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)

    return None


def _event_is_within_lookback(event: dict[str, Any], cutoff: datetime | None) -> bool:
    if cutoff is None:
        return True

    timestamp_value = _first_value(
        event,
        [
            "event_time",
            "timestamp",
            "created_at",
            "recorded_at",
            "decision_time",
            "time",
        ],
    )
    event_timestamp = _parse_event_timestamp(timestamp_value)
    if event_timestamp is None:
        return True
    return event_timestamp >= cutoff


@timeit
def get(client: ZentralSantaClient, source_name: str) -> list[dict[str, Any]]:
    events = list(client.export_santa_events(source_name))
    logger.info("Retrieved %d Santa execution events from Zentral", len(events))
    return events


@timeit
def transform_events(
    event_rows: list[dict[str, Any]],
    source_name: str,
    lookback_days: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    cutoff: datetime | None = None
    if lookback_days > 0:
        cutoff = datetime.now(tz=timezone.utc) - timedelta(days=lookback_days)

    applications_by_id: dict[str, dict[str, Any]] = {}
    versions: list[dict[str, Any]] = []
    seen_version_rows: set[tuple[str, str | None, str | None]] = set()

    for event in event_rows:
        if not _event_is_within_lookback(event, cutoff):
            continue

        application_identifier = _extract_application_identifier(event)
        if not application_identifier:
            logger.debug("Skipping Santa event without application identifier")
            continue

        application_name = _extract_application_name(event) or application_identifier
        application_id = _normalize_identifier(application_identifier)
        app_version = _extract_application_version(event)
        app_version_id = (
            f"{application_id}:{_normalize_identifier(app_version)}"
            if app_version
            else f"{application_id}:unknown"
        )

        applications_by_id[application_id] = {
            "id": application_id,
            "name": application_name,
            "identifier": application_identifier,
            "source_name": source_name,
        }

        machine_id = _extract_machine_id(event)
        executed_by_user_id = _extract_user_id(event)
        dedupe_key = (app_version_id, machine_id, executed_by_user_id)
        if dedupe_key in seen_version_rows:
            continue
        seen_version_rows.add(dedupe_key)

        version_row: dict[str, Any] = {
            "id": app_version_id,
            "version": app_version,
            "application_id": application_id,
            "source_name": source_name,
        }

        event_time = _first_value(
            event,
            [
                "event_time",
                "timestamp",
                "created_at",
                "recorded_at",
                "decision_time",
                "time",
            ],
        )
        if event_time:
            version_row["last_seen"] = event_time

        if machine_id:
            version_row["machine_id"] = machine_id
        if executed_by_user_id:
            version_row["executed_by_user_id"] = executed_by_user_id

        versions.append(version_row)

    return list(applications_by_id.values()), versions


@timeit
def load_applications(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    update_tag: int,
) -> None:
    logger.info("Loading %d Santa observed applications into Neo4j", len(data))
    load(
        neo4j_session,
        SantaObservedApplicationSchema(),
        data,
        lastupdated=update_tag,
    )


@timeit
def load_application_versions(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    update_tag: int,
) -> None:
    logger.info("Loading %d Santa observed application versions into Neo4j", len(data))
    load(
        neo4j_session,
        SantaObservedApplicationVersionSchema(),
        data,
        lastupdated=update_tag,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    logger.debug("Running SantaObservedApplication cleanup")
    GraphJob.from_node_schema(
        SantaObservedApplicationSchema(), common_job_parameters
    ).run(
        neo4j_session,
    )
    logger.debug("Running SantaObservedApplicationVersion cleanup")
    GraphJob.from_node_schema(
        SantaObservedApplicationVersionSchema(),
        common_job_parameters,
    ).run(
        neo4j_session,
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: ZentralSantaClient,
    source_name: str,
    lookback_days: int,
    common_job_parameters: dict[str, Any],
) -> None:
    event_rows = get(client, source_name)
    applications, versions = transform_events(event_rows, source_name, lookback_days)

    update_tag = int(common_job_parameters["UPDATE_TAG"])
    load_applications(neo4j_session, applications, update_tag)
    load_application_versions(neo4j_session, versions, update_tag)
    cleanup(neo4j_session, common_job_parameters)
