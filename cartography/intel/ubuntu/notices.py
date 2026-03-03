import logging
from typing import Any

import neo4j
from requests import Session

from cartography.client.core.tx import load
from cartography.client.core.tx import read_single_value_tx
from cartography.client.core.tx import run_write_query
from cartography.models.ubuntu.notices import UbuntuSecurityNoticeSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)
_TIMEOUT = (60, 60)
_PAGE_SIZE = 20
_SYNC_METADATA_ID = "UbuntuNotice_sync_metadata"
_EPOCH = "2020-01-01T00:00:00+00:00"


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_url: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    logger.info("Starting Ubuntu Security Notice sync")

    last_published = get_last_sync_timestamp(neo4j_session) or _EPOCH
    logger.info("Syncing Ubuntu notices published since %s", last_published)
    raw_notices = get_new_since(api_url, last_published)

    if raw_notices:
        transformed = transform(raw_notices)
        load_notices(neo4j_session, transformed, update_tag)

        latest_pub = _extract_latest_published(raw_notices)
        if latest_pub:
            save_sync_metadata(neo4j_session, latest_pub, update_tag)
    else:
        logger.info("No new notices found")

    # Cleanup is intentionally omitted: notices are permanent records in Ubuntu's database
    # and are never deleted. This module uses incremental sync (watermark-based), so running
    # GraphJob cleanup would incorrectly remove nodes not present in the latest partial batch.
    logger.info("Completed Ubuntu Security Notice sync")


def get_last_sync_timestamp(neo4j_session: neo4j.Session) -> str | None:
    query = """
    MATCH (s:UbuntuSyncMetadata {id: $sync_id})
    RETURN s.last_published AS last_published
    """
    result = read_single_value_tx(neo4j_session, query, sync_id=_SYNC_METADATA_ID)
    return result


def save_sync_metadata(
    neo4j_session: neo4j.Session,
    last_published: str,
    update_tag: int,
) -> None:
    query = """
    MERGE (s:UbuntuSyncMetadata {id: $sync_id})
    ON CREATE SET s.firstseen = timestamp()
    SET s.last_published = $last_published,
        s.lastupdated = $update_tag
    """
    run_write_query(
        neo4j_session,
        query,
        sync_id=_SYNC_METADATA_ID,
        last_published=last_published,
        update_tag=update_tag,
    )


def _extract_latest_published(raw_notices: list[dict[str, Any]]) -> str | None:
    timestamps = [
        notice["published"] for notice in raw_notices
        if notice.get("published") is not None
    ]
    if not timestamps:
        return None
    return max(timestamps)


@timeit
def get_new_since(api_url: str, last_published: str) -> list[dict[str, Any]]:
    new_notices: list[dict[str, Any]] = []
    offset = 0
    session = Session()
    while True:
        logger.debug("Fetching new Ubuntu notices at offset %d", offset)
        response = session.get(
            f"{api_url}/security/notices.json",
            params={
                "limit": str(_PAGE_SIZE),
                "offset": str(offset),
                "order": "newest",
            },
            timeout=_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
        notices = data.get("notices", [])
        if not notices:
            break

        found_old = False
        for notice in notices:
            pub = notice.get("published")
            if pub is None or pub <= last_published:
                found_old = True
                break
            new_notices.append(notice)

        if found_old:
            break
        offset += _PAGE_SIZE

    logger.info("Incremental sync fetched %d new Ubuntu notices", len(new_notices))
    return new_notices


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
            "cves_ids": notice.get("cves_ids", []),
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
    )
