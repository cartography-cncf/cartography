import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.wiz.api import get_paginated
from cartography.intel.wiz.util import epoch_days_ago_iso
from cartography.intel.wiz.util import filter_by_project_ids
from cartography.models.wiz.issues import WizIssueSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

_QUERY = """
query WizIssues($first: Int, $after: String, $filterBy: IssueFilters, $orderBy: IssueOrder) {
  issuesV2(filterBy: $filterBy, first: $first, after: $after, orderBy: $orderBy) {
    nodes {
      id
      createdAt
      updatedAt
      dueAt
      resolvedAt
      statusChangedAt
      status
      severity
      type
      control {
        id
        name
        description
        resolutionRecommendation
      }
      sourceRule { id name }
      project { id name slug }
      entitySnapshot {
        id
        type
        nativeType
        name
        status
        cloudPlatform
        cloudProviderURL
        providerId
        region
        resourceGroupExternalId
        subscriptionExternalId
        subscriptionName
        externalId
      }
      serviceTickets { externalId name url }
    }
    pageInfo { hasNextPage endCursor }
  }
}
"""


@timeit
def get(
    session: requests.Session,
    graphql_url: str,
    token: str,
    since_iso: str,
    project_id_filter: list[str] | None = None,
) -> list[dict[str, Any]]:
    raw = get_paginated(
        session,
        graphql_url,
        token,
        _QUERY,
        "issuesV2",
        filter_by={
            "createdAt": {"after": since_iso},
            "status": ["OPEN", "IN_PROGRESS", "RESOLVED", "REJECTED"],
            "severity": ["INFORMATIONAL", "LOW", "MEDIUM", "HIGH", "CRITICAL"],
            "type": ["TOXIC_COMBINATION", "THREAT_DETECTION", "CLOUD_CONFIGURATION"],
        },
    )
    return filter_by_project_ids(raw, project_id_filter)


def transform(raw_issues: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for issue in raw_issues:
        control = issue.get("control") or {}
        source_rule = issue.get("sourceRule") or {}
        project = issue.get("project") or {}
        resource = issue.get("entitySnapshot") or {}
        service_tickets = issue.get("serviceTickets") or []

        result.append(
            {
                "id": issue["id"],
                "name": source_rule.get("name") or control.get("name"),
                "status": issue.get("status"),
                "severity": issue.get("severity"),
                "issue_type": issue.get("type"),
                "created_at": issue.get("createdAt"),
                "updated_at": issue.get("updatedAt"),
                "due_at": issue.get("dueAt"),
                "resolved_at": issue.get("resolvedAt"),
                "status_changed_at": issue.get("statusChangedAt"),
                "control_id": control.get("id"),
                "control_name": control.get("name"),
                "control_description": control.get("description"),
                "resolution_recommendation": control.get("resolutionRecommendation"),
                "source_rule_id": source_rule.get("id"),
                "source_rule_name": source_rule.get("name"),
                "resource_id": resource.get("id"),
                "resource_name": resource.get("name"),
                "resource_type": resource.get("type"),
                "resource_native_type": resource.get("nativeType"),
                "resource_cloud_platform": resource.get("cloudPlatform"),
                "resource_external_id": resource.get("externalId")
                or resource.get("providerId"),
                "project_ids": [project["id"]] if project.get("id") else [],
                "project_names": [project["name"]] if project.get("name") else [],
                "service_ticket_urls": [
                    ticket["url"]
                    for ticket in service_tickets
                    if isinstance(ticket, dict) and ticket.get("url")
                ],
            },
        )
    return result


@timeit
def load_issues(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    tenant_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        WizIssueSchema(),
        data,
        lastupdated=update_tag,
        WIZ_TENANT_ID=tenant_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(WizIssueSchema(), common_job_parameters).run(
        neo4j_session,
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    session: requests.Session,
    graphql_url: str,
    token: str,
    tenant_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
    lookback_days: int,
    project_id_filter: list[str] | None = None,
    *,
    do_cleanup: bool = True,
) -> None:
    logger.info("Syncing Wiz issues for tenant %s", tenant_id)
    since_iso = epoch_days_ago_iso(update_tag, lookback_days)
    raw_issues = get(session, graphql_url, token, since_iso, project_id_filter)
    issues = transform(raw_issues)
    load_issues(neo4j_session, issues, tenant_id, update_tag)
    if do_cleanup:
        cleanup(neo4j_session, common_job_parameters)
