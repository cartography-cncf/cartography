import logging
from collections.abc import Iterator
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.client.core.tx import read_single_value_tx
from cartography.client.core.tx import run_write_query
from cartography.intel.ubuntu.feed import FEED_ID
from cartography.intel.ubuntu.util import retryable_session
from cartography.models.ubuntu.notices import UbuntuSecurityNoticeSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)
_TIMEOUT = (60, 60)
_PAGE_SIZE = 20
_SYNC_METADATA_ID = "UbuntuNotice_sync_metadata"


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_url: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    logger.info("Starting Ubuntu Security Notice sync")

    metadata = get_sync_metadata(neo4j_session)

    if metadata["full_sync_complete"]:
        _run_incremental_sync(
            neo4j_session,
            api_url,
            update_tag,
            metadata["last_published"],
        )
    else:
        _run_full_sync(neo4j_session, api_url, update_tag, metadata["full_sync_offset"])

    logger.info("Completed Ubuntu Security Notice sync")


def _run_full_sync(
    neo4j_session: neo4j.Session,
    api_url: str,
    update_tag: int,
    start_offset: int,
) -> None:
    if start_offset > 0:
        logger.info("Resuming full notice sync from offset %d", start_offset)
    else:
        logger.info("Running full notice ingestion")

    total = 0
    current_offset = start_offset
    for page in _fetch_notices(api_url, start_offset=start_offset):
        transformed = transform(page)
        load_notices(neo4j_session, transformed, update_tag)
        total += len(transformed)
        current_offset += _PAGE_SIZE
        save_sync_metadata(
            neo4j_session,
            update_tag,
            full_sync_complete=False,
            full_sync_offset=current_offset,
            last_published=None,
        )

    watermark = _get_max_published(neo4j_session)
    save_sync_metadata(
        neo4j_session,
        update_tag,
        full_sync_complete=True,
        full_sync_offset=0,
        last_published=watermark,
    )
    logger.info(
        "Full sync complete: loaded %d Ubuntu notices (watermark=%s)",
        total,
        watermark,
    )


def _run_incremental_sync(
    neo4j_session: neo4j.Session,
    api_url: str,
    update_tag: int,
    last_published: str | None,
) -> None:
    logger.info("Running incremental notice sync (watermark=%s)", last_published)

    total = 0
    best_watermark: str | None = None
    for page in _fetch_notices(api_url, since=last_published):
        transformed = transform(page)
        load_notices(neo4j_session, transformed, update_tag)
        total += len(transformed)
        latest_pub = _extract_latest_published(page)
        if latest_pub and (best_watermark is None or latest_pub > best_watermark):
            best_watermark = latest_pub

    if best_watermark:
        save_sync_metadata(
            neo4j_session,
            update_tag,
            full_sync_complete=True,
            full_sync_offset=0,
            last_published=best_watermark,
        )
        logger.info(
            "Incremental sync complete: loaded %d notices (new watermark=%s)",
            total,
            best_watermark,
        )
    else:
        logger.info("No new notices found")


def get_sync_metadata(neo4j_session: neo4j.Session) -> dict[str, Any]:
    def _read_tx(tx: neo4j.ManagedTransaction) -> neo4j.Record | None:
        return tx.run(
            """
            MATCH (s:UbuntuSyncMetadata {id: $sync_id})
            RETURN s.full_sync_complete AS full_sync_complete,
                   s.full_sync_offset AS full_sync_offset,
                   s.last_published AS last_published
            """,
            sync_id=_SYNC_METADATA_ID,
        ).single()

    result = neo4j_session.execute_read(_read_tx)
    if result is None:
        return {
            "full_sync_complete": False,
            "full_sync_offset": 0,
            "last_published": None,
        }
    return {
        "full_sync_complete": result["full_sync_complete"] or False,
        "full_sync_offset": result["full_sync_offset"] or 0,
        "last_published": result["last_published"],
    }


def save_sync_metadata(
    neo4j_session: neo4j.Session,
    update_tag: int,
    *,
    full_sync_complete: bool,
    full_sync_offset: int,
    last_published: str | None,
) -> None:
    query = """
    MERGE (s:UbuntuSyncMetadata {id: $sync_id})
    ON CREATE SET s.firstseen = timestamp()
    SET s.full_sync_complete = $full_sync_complete,
        s.full_sync_offset = $full_sync_offset,
        s.last_published = $last_published,
        s.lastupdated = $update_tag
    """
    run_write_query(
        neo4j_session,
        query,
        sync_id=_SYNC_METADATA_ID,
        full_sync_complete=full_sync_complete,
        full_sync_offset=full_sync_offset,
        last_published=last_published,
        update_tag=update_tag,
    )


def _extract_latest_published(raw_notices: list[dict[str, Any]]) -> str | None:
    timestamps = [
        notice["published"]
        for notice in raw_notices
        if notice.get("published") is not None
    ]
    if not timestamps:
        return None
    return max(timestamps)


def _get_max_published(neo4j_session: neo4j.Session) -> str | None:
    result = read_single_value_tx(
        neo4j_session,
        "MATCH (n:UbuntuSecurityNotice) RETURN max(n.published) AS max_published",
    )
    return str(result) if result is not None else None


@timeit
def _fetch_notices(
    api_url: str,
    *,
    since: str | None = None,
    start_offset: int = 0,
) -> Iterator[list[dict[str, Any]]]:
    """Yield pages of notices from the Ubuntu Security API.

    Full sync (since=None): fetches all notices sorted by published date ascending,
    starting from start_offset for resume capability.

    Incremental (since set): fetches notices published after the watermark, sorted
    by published date descending, stopping when it reaches already-seen data.
    """
    offset = start_offset
    total_fetched = 0
    session = retryable_session()

    if since is None:
        params_base: dict[str, str] = {"limit": str(_PAGE_SIZE), "order": "oldest"}
    else:
        params_base = {"limit": str(_PAGE_SIZE), "order": "newest"}

    while True:
        logger.debug("Fetching Ubuntu notices at offset %d", offset)
        response = session.get(
            f"{api_url}/security/notices.json",
            params={**params_base, "offset": str(offset)},
            timeout=_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
        notices = data.get("notices", [])
        if not notices:
            break

        if since is not None:
            page: list[dict[str, Any]] = []
            found_old = False
            for notice in notices:
                pub = notice.get("published")
                if pub is None or pub <= since:
                    found_old = True
                    break
                page.append(notice)

            if page:
                yield page
                total_fetched += len(page)

            if found_old:
                break
        else:
            yield notices
            total_fetched += len(notices)
            if total_fetched + start_offset >= data.get("total_results", 0):
                break

        offset += _PAGE_SIZE

    logger.debug("Fetched %d Ubuntu notices", total_fetched)


@timeit
def transform(raw_notices: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for notice in raw_notices:
        transformed = {
            "id": notice["id"],
            "title": notice.get("title"),
            "summary": notice.get("summary"),
            "description": notice.get("description"),
            "published": notice.get("published"),
            "notice_type": notice.get("type"),
            "instructions": notice.get("instructions"),
            "is_hidden": notice.get("is_hidden"),
            "cves_ids": [f"USV|{cid}" for cid in (notice.get("cves_ids") or [])],
        }
        result.append(transformed)
    return result


def load_notices(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        UbuntuSecurityNoticeSchema(),
        data,
        lastupdated=update_tag,
        FEED_ID=FEED_ID,
    )
