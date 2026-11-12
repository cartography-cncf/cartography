import logging
from datetime import datetime
from typing import Any

from cartography.intel.common.object_store import filter_report_refs
from cartography.intel.common.object_store import read_json_report
from cartography.intel.common.object_store import ReportReader

logger = logging.getLogger(__name__)

PROVIDER = "onepassword"
SUPPORTED_SCHEMA_MAJOR_VERSION = "1"


class SnapshotError(ValueError):
    """A snapshot source that Cartography refuses to ingest, with a stable reason."""

    def __init__(self, reason: str, message: str) -> None:
        super().__init__(message)
        self.reason = reason


NO_SNAPSHOT = "no_snapshot"
NOT_A_SNAPSHOT = "not_a_snapshot"
UNSUPPORTED_VERSION = "unsupported_version"
INCOMPLETE = "incomplete"
CONFLICTING_SCOPE = "conflicting_scope"

_REQUIRED_FIELDS: dict[str, type] = {
    "account_id": str,
    "collected_at": str,
    "snapshot_id": str,
    "collector": dict,
    "scope": dict,
    "users": list,
    "groups": list,
    "group_memberships": list,
    "vaults": list,
    "vault_user_grants": list,
    "vault_group_grants": list,
    "items": list,
}


def validate_snapshot(snapshot: Any, source_uri: str) -> dict[str, Any]:
    # A snapshot describes the complete access state of its vault scope, so a
    # partial or unknown document must never reach the graph: its absences
    # would be cleaned up as revoked access.
    if not isinstance(snapshot, dict) or snapshot.get("provider") != PROVIDER:
        raise SnapshotError(
            NOT_A_SNAPSHOT,
            f"{source_uri} is not a 1Password collector snapshot.",
        )
    schema_version = snapshot["schema_version"]
    if schema_version.split(".")[0] != SUPPORTED_SCHEMA_MAJOR_VERSION:
        raise SnapshotError(
            UNSUPPORTED_VERSION,
            f"{source_uri} uses unsupported snapshot schema version {schema_version}.",
        )
    if snapshot["status"] != "complete":
        raise SnapshotError(INCOMPLETE, f"{source_uri} is not a complete snapshot.")
    # Check the shape of every snapshot before any account syncs, so a
    # malformed one stops the run instead of failing after others loaded.
    malformed = sorted(
        field
        for field, field_type in _REQUIRED_FIELDS.items()
        if not isinstance(snapshot.get(field), field_type)
    )
    if not malformed:
        try:
            _collected_at(snapshot)
        except ValueError:
            malformed.append("collected_at")
        vault_ids = {vault.get("id") for vault in snapshot["vaults"]}
        if not vault_ids or vault_ids != set(snapshot["scope"].get("vault_ids", [])):
            malformed.append("vaults")
    if malformed:
        raise SnapshotError(
            NOT_A_SNAPSHOT,
            f"{source_uri} has missing or malformed fields: {', '.join(malformed)}.",
        )
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
        raise SnapshotError(
            NO_SNAPSHOT,
            f"No 1Password snapshots found in {reader.source_uri}.",
        )

    newest: dict[str, dict[str, Any]] = {}
    for ref in refs:
        snapshot = validate_snapshot(read_json_report(reader, ref), ref.uri)
        account_id = snapshot["account_id"]
        current = newest.get(account_id)
        # Two collectors with different vault scopes for one account would
        # take turns deleting each other's vaults.
        if current is not None and set(current["scope"]["vault_ids"]) != set(
            snapshot["scope"]["vault_ids"]
        ):
            raise SnapshotError(
                CONFLICTING_SCOPE,
                f"Snapshots for 1Password account {account_id} in "
                f"{reader.source_uri} cover different vaults. Run one collector "
                "per account, or remove the snapshots for the old scope.",
            )
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
