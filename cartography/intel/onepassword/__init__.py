import logging
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

    for snapshot in snapshots:
        sync_account(neo4j_session, snapshot, config.update_tag)


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
    snapshot: dict[str, Any],
    update_tag: int,
) -> None:
    account_id = snapshot["account_id"]
    logger.info(
        "Syncing 1Password account %s from snapshot %s collected at %s",
        account_id,
        snapshot["snapshot_id"],
        snapshot["collected_at"],
    )
    common_job_parameters = {"UPDATE_TAG": update_tag, "ACCOUNT_ID": account_id}

    load_account(neo4j_session, snapshot, update_tag)
    cartography.intel.onepassword.groups.sync(
        neo4j_session, snapshot, update_tag, common_job_parameters
    )
    cartography.intel.onepassword.users.sync(
        neo4j_session, snapshot, update_tag, common_job_parameters
    )
    cartography.intel.onepassword.vaults.sync(
        neo4j_session, snapshot, update_tag, common_job_parameters
    )
    cartography.intel.onepassword.items.sync(
        neo4j_session, snapshot, update_tag, common_job_parameters
    )
