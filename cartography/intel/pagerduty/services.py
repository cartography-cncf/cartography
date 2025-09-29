import logging
from typing import Any
from typing import Dict
from typing import List

import dateutil.parser
import neo4j
from pdpyras import APISession

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
    pd_session: APISession,
    common_job_parameters: dict[str, Any],
) -> None:
    services = get_services(pd_session)
    transformed_services = transform_services(services)
    load_service_data(neo4j_session, transformed_services, update_tag)
    integrations = get_integrations(pd_session, services)
    load_integration_data(neo4j_session, integrations, update_tag)
    cleanup(neo4j_session, common_job_parameters)


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


def transform_services(
    services: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Transform service data to match the schema.
    """
    transformed_services = []
    for service in services:
        if isinstance(service.get("created_at"), str):
            created_at = dateutil.parser.parse(service["created_at"])
            service["created_at"] = int(created_at.timestamp())
        service["teams_id"] = [team["id"] for team in service.get("teams", [])]
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
