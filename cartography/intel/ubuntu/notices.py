import logging
from typing import Any

import neo4j
from requests import Session

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.ubuntu.notices import UbuntuSecurityNoticeSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)
_TIMEOUT = (60, 60)
_PAGE_SIZE = 20


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_url: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    logger.info("Starting Ubuntu Security Notice sync")
    raw_notices = get(api_url)
    transformed = transform(raw_notices)
    load_notices(neo4j_session, transformed, update_tag)
    cleanup(neo4j_session, common_job_parameters)
    logger.info("Completed Ubuntu Security Notice sync")


@timeit
def get(api_url: str) -> list[dict[str, Any]]:
    all_notices: list[dict[str, Any]] = []
    offset = 0
    session = Session()
    while True:
        logger.debug("Fetching Ubuntu Security Notices at offset %d", offset)
        response = session.get(
            f"{api_url}/security/notices.json",
            params={"limit": _PAGE_SIZE, "offset": offset, "order": "oldest"},
            timeout=_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
        notices = data.get("notices", [])
        all_notices.extend(notices)
        total = data.get("total_results", 0)
        if not notices or len(all_notices) >= total:
            break
        offset += _PAGE_SIZE
    logger.debug("Fetched %d Ubuntu Security Notices total", len(all_notices))
    return all_notices


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


def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(UbuntuSecurityNoticeSchema(), common_job_parameters).run(
        neo4j_session,
    )
