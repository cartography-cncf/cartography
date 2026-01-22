import logging
from typing import Any
from typing import Dict
from typing import List

import dateutil.parser
import neo4j
from pagerduty import RestApiV2Client

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.pagerduty.integration import PagerDutyIntegrationSchema
from cartography.models.pagerduty.service import PagerDutyServiceSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync_services(
    neo4j_session: neo4j.Session,
    update_tag: int,
    pd_session: RestApiV2Client,
    common_job_parameters: dict[str, Any],
) -> None:
    services = get_services(pd_session)
    transformed_services = transform_services(services)
    load_service_data(neo4j_session, transformed_services, update_tag)
    integrations = get_integrations(pd_session, services)
    load_integration_data(neo4j_session, integrations, update_tag)
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get_services(pd_session: RestApiV2Client) -> List[Dict[str, Any]]:
    all_services: List[Dict[str, Any]] = []
    for service in pd_session.iter_all("services"):
        all_services.append(service)
    return all_services


@timeit
def get_integrations(
    pd_session: RestApiV2Client,
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


def transform_services(
    services: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Transform service data to match the schema.
    Flattens nested objects (incident_urgency_rule, support_hours, alert_grouping_parameters)
    to top-level keys expected by PagerDutyServiceSchema.
    """
    transformed_services = []
    for service in services:
        if isinstance(service.get("created_at"), str):
            created_at = dateutil.parser.parse(service["created_at"])
            service["created_at"] = int(created_at.timestamp())
        service["teams_id"] = [team["id"] for team in service.get("teams", [])]

        # Flatten alert_grouping_parameters
        # Use `or {}` to handle both missing keys and explicit None values
        alert_grouping = service.get("alert_grouping_parameters") or {}
        service["alert_grouping_parameters_type"] = alert_grouping.get("type")

        # Flatten incident_urgency_rule
        urgency_rule = service.get("incident_urgency_rule") or {}
        service["incident_urgency_rule_type"] = urgency_rule.get("type")

        during_support = urgency_rule.get("during_support_hours") or {}
        service["incident_urgency_rule_during_support_hours_type"] = during_support.get(
            "type"
        )
        service["incident_urgency_rule_during_support_hours_urgency"] = (
            during_support.get("urgency")
        )

        outside_support = urgency_rule.get("outside_support_hours") or {}
        service["incident_urgency_rule_outside_support_hours_type"] = (
            outside_support.get("type")
        )
        service["incident_urgency_rule_outside_support_hours_urgency"] = (
            outside_support.get("urgency")
        )

        # Flatten support_hours
        support_hours = service.get("support_hours") or {}
        service["support_hours_type"] = support_hours.get("type")
        service["support_hours_time_zone"] = support_hours.get("time_zone")
        service["support_hours_start_time"] = support_hours.get("start_time")
        service["support_hours_end_time"] = support_hours.get("end_time")
        service["support_hours_days_of_week"] = support_hours.get("days_of_week")

        transformed_services.append(service)
    return transformed_services


@timeit
def load_service_data(
    neo4j_session: neo4j.Session,
    data: List[Dict],
    update_tag: int,
) -> None:
    """
    Transform and load service information
    """
    logger.info(f"Loading {len(data)} pagerduty services.")
    load(
        neo4j_session,
        PagerDutyServiceSchema(),
        data,
        lastupdated=update_tag,
    )


def load_integration_data(
    neo4j_session: neo4j.Session,
    data: List[Dict],
    update_tag: int,
) -> None:
    """
    Transform and load integration information
    """
    for integration in data:
        created_at = dateutil.parser.parse(integration["created_at"])
        integration["created_at"] = int(created_at.timestamp())

    logger.info(f"Loading {len(data)} pagerduty integrations.")
    load(
        neo4j_session,
        PagerDutyIntegrationSchema(),
        data,
        lastupdated=update_tag,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(PagerDutyIntegrationSchema(), common_job_parameters).run(
        neo4j_session,
    )
    GraphJob.from_node_schema(PagerDutyServiceSchema(), common_job_parameters).run(
        neo4j_session,
    )
