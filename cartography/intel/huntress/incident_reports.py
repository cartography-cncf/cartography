import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.huntress.util import get_paginated_huntress_items
from cartography.intel.huntress.util import required_id
from cartography.models.huntress.incident_report import HuntressIncidentReportSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get(api_session: requests.Session, base_uri: str) -> list[dict[str, Any]]:
    return get_paginated_huntress_items(
        api_session,
        base_uri,
        "incident_reports",
        "incident_reports",
    )


def _remediation_types(remediations: Any) -> list[str]:
    """Collect the distinct remediation types listed on an incident report.

    The API inlines only the first ten remediations, so this is a summary of what the SOC
    proposed rather than an exhaustive list. Sorted so a re-sync of unchanged data does
    not rewrite the property.
    """
    if not isinstance(remediations, dict):
        return []
    items = remediations.get("items")
    if not isinstance(items, list):
        return []
    return sorted(
        {
            item["type"]
            for item in items
            if isinstance(item, dict) and item.get("type") is not None
        }
    )


def transform(api_result: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for report in api_result:
        remediations = report.get("remediations")
        result.append(
            {
                "id": required_id(report, "IncidentReport"),
                "organization_id": report.get("organization_id"),
                "agent_id": report.get("agent_id"),
                "subject": report.get("subject"),
                "body": report.get("body"),
                "summary": report.get("summary"),
                "severity": report.get("severity"),
                "status": report.get("status"),
                "platform": report.get("platform"),
                # `indicator_counts` maps each indicator type to a count. Neo4j cannot
                # store a map as a property, so only the type list is kept.
                "indicator_types": report.get("indicator_types"),
                "remediation_count": (
                    remediations.get("total_count")
                    if isinstance(remediations, dict)
                    else None
                ),
                "remediation_types": _remediation_types(remediations),
                "sent_at": report.get("sent_at"),
                "closed_at": report.get("closed_at"),
                "status_updated_at": report.get("status_updated_at"),
                "updated_at": report.get("updated_at"),
            }
        )
    return result


def load_incident_reports(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    account_id: int,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        HuntressIncidentReportSchema(),
        data,
        lastupdated=update_tag,
        ACCOUNT_ID=account_id,
    )


def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(
        HuntressIncidentReportSchema(), common_job_parameters
    ).run(neo4j_session)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    base_uri: str,
    account_id: int,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    raw_data = get(api_session, base_uri)
    incident_reports = transform(raw_data)
    load_incident_reports(neo4j_session, incident_reports, account_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)
