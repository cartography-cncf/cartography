import logging
from typing import Any

import neo4j
import requests
from dateutil import parser as dt_parse

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.sentry.util import get_paginated_results
from cartography.models.sentry.release import SentryReleaseSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    org_id: str,
    org_slug: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
    base_url: str,
) -> None:
    raw_releases = get(api_session, base_url, org_slug)
    transformed = transform(raw_releases)
    load_releases(neo4j_session, transformed, org_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(
    api_session: requests.Session,
    base_url: str,
    org_slug: str,
) -> list[dict[str, Any]]:
    return get_paginated_results(
        api_session,
        f"{base_url}/organizations/{org_slug}/releases/",
    )


@timeit
def transform(raw_releases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for release in raw_releases:
        r = release.copy()
        # Use version as id since release "id" is an integer that may collide across orgs
        r["id"] = release["version"]
        r["date_created"] = _to_epoch_ms(release.get("dateCreated"))
        r["date_released"] = _to_epoch_ms(release.get("dateReleased"))
        result.append(r)
    return result


def load_releases(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    org_id: str,
    update_tag: int,
) -> None:
    logger.info("Loading %d SentryRelease(s) into Neo4j.", len(data))
    load(
        neo4j_session,
        SentryReleaseSchema(),
        data,
        lastupdated=update_tag,
        ORG_ID=org_id,
    )


def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(SentryReleaseSchema(), common_job_parameters).run(
        neo4j_session,
    )


def _to_epoch_ms(date_str: str | None) -> int | None:
    if not date_str:
        return None
    return int(dt_parse.parse(date_str).timestamp() * 1000)
