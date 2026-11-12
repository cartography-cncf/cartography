import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import neo4j

import cartography.intel.onepassword.groups
import cartography.intel.onepassword.items
import cartography.intel.onepassword.snapshots
import cartography.intel.onepassword.users
import cartography.intel.onepassword.vaults
from cartography.client.core.tx import load
from cartography.config import Config
from cartography.intel.common.report_reader_builder import (
    build_report_reader_for_source,
)
from cartography.intel.common.report_source import parse_report_source
from cartography.models.onepassword.account import OnePasswordAccountSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

Rows = list[dict[str, Any]]


@dataclass(frozen=True)
class PreparedAccount:
    """Every row one account loads, built before the graph changes."""

    snapshot: dict[str, Any]
    groups: Rows
    users: Rows
    service_accounts: Rows
    vaults: Rows
    grants: tuple[Rows, Rows, Rows]
    items: Rows


@timeit
def start_onepassword_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    if not config.onepassword_source:
        logger.info(
            "1Password import is not configured - skipping this module. "
            "See docs to configure.",
        )
        return

    source = parse_report_source(config.onepassword_source)
    with build_report_reader_for_source(source, config=config) as reader:
        snapshots = cartography.intel.onepassword.snapshots.get(reader)

    # Transform every account first, so a malformed snapshot fails the run
    # before any account's graph data changes.
    accounts = [prepare(snapshot) for snapshot in snapshots]
    for account in accounts:
        sync_account(neo4j_session, account, config.update_tag)


def prepare(snapshot: dict[str, Any]) -> PreparedAccount:
    users, service_accounts = cartography.intel.onepassword.users.transform(snapshot)
    return PreparedAccount(
        snapshot=snapshot,
        groups=cartography.intel.onepassword.groups.transform(snapshot),
        users=users,
        service_accounts=service_accounts,
        vaults=cartography.intel.onepassword.vaults.transform_vaults(snapshot),
        grants=cartography.intel.onepassword.vaults.transform_grants(snapshot),
        items=cartography.intel.onepassword.items.transform(snapshot),
    )


def get_ingested_collected_at(
    neo4j_session: neo4j.Session,
    account_id: str,
) -> str | None:
    record = neo4j_session.run(
        "MATCH (a:OnePasswordAccount {id: $account_id}) "
        "RETURN a.snapshot_collected_at AS collected_at",
        account_id=account_id,
    ).single()
    return record["collected_at"] if record else None


def load_account(
    neo4j_session: neo4j.Session,
    snapshot: dict[str, Any],
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        OnePasswordAccountSchema(),
        [
            {
                "id": snapshot["account_id"],
                "snapshot_id": snapshot["snapshot_id"],
                "snapshot_collected_at": snapshot["collected_at"],
                "collector_version": snapshot["collector"]["version"],
                "vault_scope": snapshot["scope"]["vault_ids"],
            },
        ],
        lastupdated=update_tag,
    )


@timeit
def sync_account(
    neo4j_session: neo4j.Session,
    account: PreparedAccount,
    update_tag: int,
) -> None:
    snapshot = account.snapshot
    account_id = snapshot["account_id"]
    ingested_at = get_ingested_collected_at(neo4j_session, account_id)
    if ingested_at is not None and datetime.fromisoformat(
        ingested_at
    ) > datetime.fromisoformat(snapshot["collected_at"]):
        # A snapshot older than the graph's would restore access that a newer
        # snapshot already revoked.
        logger.warning(
            "Skipping 1Password account %s: snapshot collected at %s is older "
            "than the ingested snapshot collected at %s.",
            account_id,
            snapshot["collected_at"],
            ingested_at,
        )
        return

    logger.info(
        "Syncing 1Password account %s from snapshot %s collected at %s",
        account_id,
        snapshot["snapshot_id"],
        snapshot["collected_at"],
    )
    common_job_parameters = {"UPDATE_TAG": update_tag, "ACCOUNT_ID": account_id}

    load_account(neo4j_session, snapshot, update_tag)
    cartography.intel.onepassword.groups.load_groups(
        neo4j_session, account.groups, account_id, update_tag
    )
    cartography.intel.onepassword.users.load_users(
        neo4j_session,
        account.users,
        account.service_accounts,
        account_id,
        update_tag,
    )
    cartography.intel.onepassword.vaults.load_vaults(
        neo4j_session, account.vaults, account.grants, account_id, update_tag
    )
    cartography.intel.onepassword.items.load_items(
        neo4j_session, account.items, account_id, update_tag
    )

    cartography.intel.onepassword.items.cleanup(neo4j_session, common_job_parameters)
    cartography.intel.onepassword.vaults.cleanup(neo4j_session, common_job_parameters)
    cartography.intel.onepassword.users.cleanup(neo4j_session, common_job_parameters)
    cartography.intel.onepassword.groups.cleanup(neo4j_session, common_job_parameters)
