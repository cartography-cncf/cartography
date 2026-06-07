from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.intel.sentry.util import call_sentry_api
from cartography.intel.sentry.util import get_paginated_results
from cartography.models.sentry.organization import SentryOrganizationSchema
from cartography.util import timeit


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    update_tag: int,
    base_url: str,
    org_slug: str | None = None,
) -> list[dict[str, Any]]:
    orgs = get(api_session, base_url, org_slug)
    transformed = transform(orgs)
    load_organizations(neo4j_session, transformed, update_tag)
    return transformed


@timeit
def get(
    api_session: requests.Session,
    base_url: str,
    org_slug: str | None = None,
) -> list[dict[str, Any]]:
    if org_slug:
        response = call_sentry_api(api_session, f"{base_url}/organizations/{org_slug}/")
        return [response.json()]
    return get_paginated_results(api_session, f"{base_url}/organizations/")


@timeit
def transform(raw_orgs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for org in raw_orgs:
        o = org.copy()
        o["id"] = org["id"]
        status = org.get("status", {})
        o["status"] = status.get("name") if isinstance(status, dict) else status
        o["date_created"] = org.get("dateCreated")
        result.append(o)
    return result


def load_organizations(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        SentryOrganizationSchema(),
        data,
        lastupdated=update_tag,
    )
