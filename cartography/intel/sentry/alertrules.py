import logging
from typing import Any

import neo4j
import requests
from dateutil import parser as dt_parse

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.sentry.util import get_paginated_results
from cartography.models.sentry.alertrule import SentryAlertRuleSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    org_slug: str,
    project: dict[str, Any],
    update_tag: int,
    common_job_parameters: dict[str, Any],
    base_url: str,
) -> None:
    project_id = project["id"]
    project_slug = project["slug"]
    raw_rules = get(api_session, base_url, org_slug, project_slug)
    transformed = transform(raw_rules, project_slug)
    load_alert_rules(neo4j_session, transformed, project_id, update_tag)
    cleanup(neo4j_session, common_job_parameters, project_id)


@timeit
def get(
    api_session: requests.Session,
    base_url: str,
    org_slug: str,
    project_slug: str,
) -> list[dict[str, Any]]:
    return get_paginated_results(
        api_session,
        f"{base_url}/projects/{org_slug}/{project_slug}/rules/",
    )


@timeit
def transform(
    raw_rules: list[dict[str, Any]],
    project_slug: str,
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for rule in raw_rules:
        r = rule.copy()
        r["id"] = rule["id"]
        r["date_created"] = _to_epoch_ms(rule.get("dateCreated"))
        r["project_slug"] = project_slug
        result.append(r)
    return result


def load_alert_rules(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    project_id: str,
    update_tag: int,
) -> None:
    logger.info("Loading %d SentryAlertRule(s) into Neo4j.", len(data))
    load(
        neo4j_session,
        SentryAlertRuleSchema(),
        data,
        lastupdated=update_tag,
        PROJECT_ID=project_id,
    )


def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
    project_id: str,
) -> None:
    # Alert rules are sub-resources of projects, so we need per-project cleanup
    params = {**common_job_parameters, "PROJECT_ID": project_id}
    GraphJob.from_node_schema(SentryAlertRuleSchema(), params).run(
        neo4j_session,
    )


def _to_epoch_ms(date_str: str | None) -> int | None:
    if not date_str:
        return None
    return int(dt_parse.parse(date_str).timestamp() * 1000)
