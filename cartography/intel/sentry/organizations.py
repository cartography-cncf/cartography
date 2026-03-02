import logging
from typing import Any

import neo4j
import requests
from dateutil import parser as dt_parse

from cartography.client.core.tx import load
from cartography.intel.sentry.util import get_paginated_results
from cartography.models.sentry.organization import SentryOrganizationSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    update_tag: int,
    base_url: str,
) -> list[dict[str, Any]]:
    orgs = get(api_session, base_url)
    transformed = transform(orgs)
    load_organizations(neo4j_session, transformed, update_tag)
    return transformed


@timeit
def get(
    api_session: requests.Session,
    base_url: str,
) -> list[dict[str, Any]]:
    return get_paginated_results(api_session, f"{base_url}/organizations/")


@timeit
def transform(raw_orgs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for org in raw_orgs:
        o = org.copy()
        o["id"] = org["id"]
        status = org.get("status", {})
        o["status"] = status.get("name") if isinstance(status, dict) else status
        o["date_created"] = _to_epoch_ms(org.get("dateCreated"))
        result.append(o)
    return result


def load_organizations(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    update_tag: int,
) -> None:
    logger.info("Loading %d SentryOrganization(s) into Neo4j.", len(data))
    load(
        neo4j_session,
        SentryOrganizationSchema(),
        data,
        lastupdated=update_tag,
    )


def _to_epoch_ms(date_str: str | None) -> int | None:
    if not date_str:
        return None
    return int(dt_parse.parse(date_str).timestamp() * 1000)
