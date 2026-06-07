from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.sentry.util import get_paginated_results
from cartography.models.sentry.release import SentryReleaseSchema
from cartography.util import timeit


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
    transformed = transform(raw_releases, org_id)
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
def transform(raw_releases: list[dict[str, Any]], org_id: str) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for release in raw_releases:
        r = release.copy()
        # Scope id to org to prevent collisions if the same version exists in multiple orgs
        r["id"] = f"{org_id}/{release['version']}"
        r["date_created"] = release.get("dateCreated")
        r["date_released"] = release.get("dateReleased")
        result.append(r)
    return result


def load_releases(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    org_id: str,
    update_tag: int,
) -> None:
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
