import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.santa.client import ZentralSantaClient
from cartography.models.santa.machine import SantaMachineSchema
from cartography.models.santa.user import SantaUserSchema
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


def _extract_machine_id(snapshot: dict[str, Any]) -> str | None:
    return _first_value(
        snapshot,
        [
            "serial_number",
            "system_info.hardware_serial",
            "imei",
            "meid",
        ],
    )


def _extract_email(principal_name: str | None) -> str | None:
    if not principal_name:
        return None
    if "@" not in principal_name:
        return None
    return principal_name.lower()


def _extract_user(principal_user: dict[str, Any]) -> tuple[str | None, dict[str, Any]]:
    principal_name = _first_value(principal_user, ["principal_name"])
    user_id = _first_value(principal_user, ["principal_name", "unique_id"])
    if not user_id:
        return None, {}

    display_name = _first_value(principal_user, ["display_name"]) or principal_name

    user_row: dict[str, Any] = {
        "id": user_id,
        "principal_name": principal_name,
        "display_name": display_name,
    }
    email = _extract_email(principal_name)
    if email:
        user_row["email"] = email

    return user_id, user_row


def _merge_non_empty(existing: dict[str, Any], updates: dict[str, Any]) -> None:
    for key, value in updates.items():
        if value not in (None, ""):
            existing[key] = value


def _format_os_version(snapshot: dict[str, Any]) -> str | None:
    os_version = snapshot.get("os_version")
    if not isinstance(os_version, dict):
        return None

    name = _first_value(os_version, ["name"])
    version_parts = [
        _first_value(os_version, ["major"]),
        _first_value(os_version, ["minor"]),
        _first_value(os_version, ["patch"]),
        _first_value(os_version, ["build"]),
    ]
    compact_version = ".".join(p for p in version_parts if p)

    if name and compact_version:
        return f"{name} {compact_version}"
    return name or compact_version or None


@timeit
def get(client: ZentralSantaClient, source_name: str) -> list[dict[str, Any]]:
    snapshots = list(client.export_machine_snapshots(source_name))
    logger.info("Retrieved %d machine snapshots from Zentral", len(snapshots))
    return snapshots


@timeit
def transform_machine_snapshots(
    machine_snapshots: list[dict[str, Any]],
    source_name: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    machine_map: dict[str, dict[str, Any]] = {}
    user_map: dict[str, dict[str, Any]] = {}

    for snapshot in machine_snapshots:
        machine_id = _extract_machine_id(snapshot)
        if not machine_id:
            logger.debug("Skipping machine snapshot without stable identifier")
            continue

        machine_source_name = (
            _first_value(snapshot, ["source.name"]) or source_name or "Santa"
        )

        machine_row: dict[str, Any] = {
            "id": machine_id,
            "hostname": _first_value(
                snapshot,
                [
                    "system_info.hostname",
                    "system_info.computer_name",
                    "serial_number",
                ],
            )
            or machine_id,
            "serial_number": _first_value(
                snapshot,
                ["serial_number", "system_info.hardware_serial"],
            )
            or machine_id,
            "platform": _first_value(snapshot, ["platform"]),
            "model": _first_value(snapshot, ["system_info.hardware_model"]),
            "os_version": _format_os_version(snapshot),
            "source_name": machine_source_name,
            "last_seen": _first_value(snapshot, ["last_seen"]),
        }

        principal_user = snapshot.get("principal_user")
        if isinstance(principal_user, dict):
            user_id, user_row = _extract_user(principal_user)
            if user_id and user_row:
                user_row["source_name"] = machine_source_name
                existing_user_row = user_map.get(user_id)
                if existing_user_row:
                    _merge_non_empty(existing_user_row, user_row)
                else:
                    user_map[user_id] = user_row
                machine_row["primary_user_id"] = user_id

        existing_machine_row = machine_map.get(machine_id)
        if existing_machine_row:
            _merge_non_empty(existing_machine_row, machine_row)
        else:
            machine_map[machine_id] = machine_row

    return list(machine_map.values()), list(user_map.values())


@timeit
def load_machines(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    update_tag: int,
) -> None:
    logger.info("Loading %d Santa machines into Neo4j", len(data))
    load(
        neo4j_session,
        SantaMachineSchema(),
        data,
        lastupdated=update_tag,
    )


@timeit
def load_users(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    update_tag: int,
) -> None:
    logger.info("Loading %d Santa users into Neo4j", len(data))
    load(
        neo4j_session,
        SantaUserSchema(),
        data,
        lastupdated=update_tag,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    logger.debug("Running SantaMachine cleanup")
    GraphJob.from_node_schema(SantaMachineSchema(), common_job_parameters).run(
        neo4j_session,
    )
    logger.debug("Running SantaUser cleanup")
    GraphJob.from_node_schema(SantaUserSchema(), common_job_parameters).run(
        neo4j_session,
    )
    # SantaUser currently has no schema-owned relationships, so GraphJob cleanup is a no-op.
    # Explicitly remove stale SantaUser nodes to keep user attribution current between sync runs.
    while True:
        result = neo4j_session.run(
            """
            MATCH (n:SantaUser)
            WHERE n.lastupdated <> $UPDATE_TAG
            WITH n LIMIT $LIMIT_SIZE
            DETACH DELETE n
            """,
            UPDATE_TAG=common_job_parameters["UPDATE_TAG"],
            LIMIT_SIZE=100,
        )
        if result.consume().counters.nodes_deleted == 0:
            break


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: ZentralSantaClient,
    source_name: str,
    common_job_parameters: dict[str, Any],
) -> None:
    machine_snapshots = get(client, source_name)
    machines, users = transform_machine_snapshots(machine_snapshots, source_name)

    update_tag = int(common_job_parameters["UPDATE_TAG"])
    load_users(neo4j_session, users, update_tag)
    load_machines(neo4j_session, machines, update_tag)
    cleanup(neo4j_session, common_job_parameters)
