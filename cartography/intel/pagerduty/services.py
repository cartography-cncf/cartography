import logging
from typing import Any
from typing import Dict
from typing import List

import dateutil.parser
import neo4j
from pdpyras import APISession

from cartography.client.core.tx import run_write_query
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync_services(
    neo4j_session: neo4j.Session,
    update_tag: int,
    pd_session: APISession,
) -> None:
    services = get_services(pd_session)
    load_service_data(neo4j_session, services, update_tag)
    integrations = get_integrations(pd_session, services)
    load_integration_data(neo4j_session, integrations, update_tag)


@timeit
def get_services(pd_session: APISession) -> List[Dict[str, Any]]:
    all_services: List[Dict[str, Any]] = []
    for service in pd_session.iter_all("services"):
        all_services.append(service)
    return all_services


@timeit
def get_integrations(
    pd_session: APISession,
    services: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Get integrations from services.
    """
    all_integrations: List[Dict[str, Any]] = []
    for service in services:
        s_id = service["id"]
        if service.get("integrations"):
            for integration in service["integrations"]:
                i_id = integration["id"]
                i = pd_session.rget(f"/services/{s_id}/integrations/{i_id}")
                all_integrations.append(i)
    return all_integrations


def load_service_data(
    neo4j_session: neo4j.Session,
    data: List[Dict],
    update_tag: int,
) -> None:
    """
    Transform and load service information
    """
    ingestion_cypher_query = """
    UNWIND $Services AS service
        MERGE (s:PagerDutyService{id: service.id})
        ON CREATE SET s.html_url = service.html_url,
            s.firstseen = timestamp()
        SET s.type = service.type,
            s.summary = service.summary,
            s.name = service.name,
            s.description = service.description,
            s.auto_resolve_timeout = service.auto_resolve_timeout,
            s.acknowledgement_timeout = service.acknowledgement_timeout,
            s.created_at = service.created_at,
            s.status = service.status,
            s.alert_creation = service.alert_creation,
            s.alert_grouping_parameters_type = service.alert_grouping_parameters_type,
            s.incident_urgency_rule_type = service.incident_urgency_rule.type,
            s.incident_urgency_rule_during_support_hours_type = service.incident_urgency_rule.during_support_hours.type,
            s.incident_urgency_rule_during_support_hours_urgency = service.incident_urgency_rule.during_support_hours.urgency,
            s.incident_urgency_rule_outside_support_hours_type = service.incident_urgency_rule.outside_support_hours.type,
            s.incident_urgency_rule_outside_support_hours_urgency = service.incident_urgency_rule.outside_support_hours.urgency,
            s.support_hours_type = service.support_hours.type,
            s.support_hours_time_zone = service.support_hours.time_zone,
            s.support_hours_start_time = s.support_hours.start_time,
            s.support_hours_end_time = s.support_hours.end_time,
            s.support_hours_days_of_week = s.support_hours.days_of_week,
            s.lastupdated = $update_tag
    """  # noqa: E501
    logger.info(f"Loading {len(data)} pagerduty services.")

    team_relations: List[Dict[str, str]] = []
    for service in data:
        created_at = dateutil.parser.parse(service["created_at"])
        service["created_at"] = int(created_at.timestamp())
        if service.get("teams"):
            for team in service["teams"]:
                team_relations.append({"service": service["id"], "team": team["id"]})

    run_write_query(
        neo4j_session,
        ingestion_cypher_query,
        Services=data,
        update_tag=update_tag,
    )

    _attach_teams(neo4j_session, team_relations, update_tag)
    # TODO: handle escalation policy mapping


def _attach_teams(
    neo4j_session: neo4j.Session,
    data: List[Dict],
    update_tag: int,
) -> None:
    """
    Add relationship between teams and services.
    """
    ingestion_cypher_query = """
    UNWIND $Relations AS relation
        MATCH (t:PagerDutyTeam{id: relation.team}), (s:PagerDutyService{id: relation.service})
        MERGE (t)-[r:ASSOCIATED_WITH]->(s)
        ON CREATE SET r.firstseen = timestamp()
    """
    run_write_query(
        neo4j_session,
        ingestion_cypher_query,
        Relations=data,
        update_tag=update_tag,
    )


def load_integration_data(
    neo4j_session: neo4j.Session,
    data: List[Dict],
    update_tag: int,
) -> None:
    """
    Transform and load integration information
    """
    ingestion_cypher_query = """
    UNWIND $Integrations AS integration
        MERGE (i:PagerDutyIntegration{id: integration.id})
        ON CREATE SET i.html_url = integration.html_url,
            i.firstseen = timestamp()
        SET i.type = integration.type,
            i.summary = integration.summary,
            i.name = integration.name,
            i.created_at = integration.created_at,
            i.lastupdated = $update_tag
        WITH i, integration
        MATCH (v:PagerDutyVendor{id: integration.vendor.id})
        MERGE (i)-[vr:HAS_VENDOR]->(v)
        ON CREATE SET vr.firstseen = timestamp()
        SET vr.lastupdated = $update_tag
        WITH i, integration
        MATCH (s:PagerDutyService{id: integration.service.id})
        MERGE (s)-[sr:HAS_INTEGRATION]->(i)
        ON CREATE SET sr.firstseen = timestamp()
        SET sr.lastupdated = $update_tag
    """
    logger.info(f"Loading {len(data)} pagerduty integrations.")

    for integration in data:
        created_at = dateutil.parser.parse(integration["created_at"])
        integration["created_at"] = int(created_at.timestamp())

    run_write_query(
        neo4j_session,
        ingestion_cypher_query,
        Integrations=data,
        update_tag=update_tag,
    )
