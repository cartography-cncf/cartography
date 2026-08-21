import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.render.util import BASE_URL
from cartography.intel.render.util import list_paginated
from cartography.intel.render.util import require_non_empty
from cartography.models.render.headerrule import RenderHeaderRuleSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get(session: requests.Session, service_id: str) -> list[dict[str, Any]]:
    return list_paginated(
        session,
        f"{BASE_URL}/services/{service_id}/headers",
        "header",
    )


def transform(
    header_rules: list[dict[str, Any]], service_id: str, owner_id: str
) -> list[dict[str, Any]]:
    return [
        {
            "id": require_non_empty(rule.get("id"), "header rule id"),
            "ownerId": owner_id,
            "serviceId": service_id,
            "path": rule.get("path"),
            "name": rule.get("name"),
            "value": rule.get("value"),
        }
        for rule in header_rules
    ]


@timeit
def load_header_rules(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    owner_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        RenderHeaderRuleSchema(),
        data,
        lastupdated=update_tag,
        OWNER_ID=owner_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(RenderHeaderRuleSchema(), common_job_parameters).run(
        neo4j_session,
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    session: requests.Session,
    owner_id: str,
    services: list[dict[str, Any]],
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    all_rules: list[dict[str, Any]] = []
    for service in services:
        # Custom response headers are a static-site-only feature: static sites have no
        # server-side component to inject headers itself, so Render manages them at
        # its edge instead (https://render.com/docs/static-site-headers). Every other
        # service type (web, private, background worker, cron) runs its own server and
        # sets headers in application code, with no comparable Render-managed feature -
        # calling this endpoint for those types is expected to 404.
        if service.get("type") != "static_site":
            continue
        service_id = service["id"]
        rules = get(session, service_id)
        all_rules.extend(transform(rules, service_id, owner_id))
    load_header_rules(neo4j_session, all_rules, owner_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)
