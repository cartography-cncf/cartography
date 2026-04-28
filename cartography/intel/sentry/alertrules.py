from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.sentry.util import get_paginated_results
from cartography.models.sentry.alertrule import SentryAlertRuleSchema
from cartography.util import timeit


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    org_id: str,
    org_slug: str,
    project: dict[str, Any],
    update_tag: int,
    base_url: str,
) -> None:
    project_id = project["id"]
    project_slug = project["slug"]
    raw_rules = get(api_session, base_url, org_slug, project_slug)
    transformed = transform(raw_rules, project_slug)
    load_alert_rules(neo4j_session, transformed, org_id, project_id, update_tag)


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
        r["date_created"] = rule.get("dateCreated")
        r["project_slug"] = project_slug
        result.append(r)
    return result


def load_alert_rules(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    org_id: str,
    project_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        SentryAlertRuleSchema(),
        data,
        lastupdated=update_tag,
        ORG_ID=org_id,
        PROJECT_ID=project_id,
    )


def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(SentryAlertRuleSchema(), common_job_parameters).run(
        neo4j_session,
    )
