import logging
from datetime import datetime
from typing import Any

from cartography.intel.common.object_store import filter_report_refs
from cartography.intel.common.object_store import read_json_report
from cartography.intel.common.object_store import ReportReader

logger = logging.getLogger(__name__)

PROVIDER = "onepassword"
SUPPORTED_SCHEMA_MAJOR_VERSION = "1"


def validate_snapshot(snapshot: Any, source_uri: str) -> dict[str, Any]:
    # A snapshot describes the complete access state of its vault scope, so a
    # partial or unknown document must never reach the graph: its absences
    # would be cleaned up as revoked access.
    if not isinstance(snapshot, dict) or snapshot.get("provider") != PROVIDER:
        raise ValueError(f"{source_uri} is not a 1Password collector snapshot.")
    schema_version = snapshot["schema_version"]
    if schema_version.split(".")[0] != SUPPORTED_SCHEMA_MAJOR_VERSION:
        raise ValueError(
            f"{source_uri} uses unsupported snapshot schema version {schema_version}.",
        )
    if snapshot["status"] != "complete":
        raise ValueError(f"{source_uri} is not a complete snapshot.")
    return snapshot


def _collected_at(snapshot: dict[str, Any]) -> datetime:
    return datetime.fromisoformat(snapshot["collected_at"])


def get(reader: ReportReader) -> list[dict[str, Any]]:
    """
    Return the newest complete snapshot for each 1Password account in the source.

    Every JSON object under the source must be a valid snapshot. One unreadable
    object stops the sync, because it could be the newest snapshot of an
    account and ingesting an older one would restore revoked access.
    """
    refs = filter_report_refs(reader.list_reports(), suffix=".json")
    if not refs:
        raise ValueError(f"No 1Password snapshots found in {reader.source_uri}.")

    newest: dict[str, dict[str, Any]] = {}
    for ref in refs:
        snapshot = validate_snapshot(read_json_report(reader, ref), ref.uri)
        account_id = snapshot["account_id"]
        current = newest.get(account_id)
        if current is None or (_collected_at(snapshot), snapshot["snapshot_id"]) > (
            _collected_at(current),
            current["snapshot_id"],
        ):
            newest[account_id] = snapshot

    if len(newest) < len(refs):
        logger.debug(
            "Selected %d of %d 1Password snapshots in %s; older snapshots of the same account are ignored.",
            len(newest),
            len(refs),
            reader.source_uri,
        )
    return [newest[account_id] for account_id in sorted(newest)]
