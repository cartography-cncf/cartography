import logging
from typing import Any

import neo4j
from azure.core.exceptions import HttpResponseError
from azure.mgmt.security import SecurityCenter

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.azure.security_center import AzureSecurityAssessmentSchema
from cartography.util import timeit

from .util.credentials import Credentials

logger = logging.getLogger(__name__)


@timeit
def get_assessments(client: SecurityCenter, subscription_id: str) -> list[dict]:
    """
    Get a list of Security Assessments from the given Azure subscription.
    """
    try:
        scope = f"subscriptions/{subscription_id}"
        return [a.as_dict() for a in client.assessments.list(scope)]
    except HttpResponseError:
        logger.warning(
            f"Failed to get Security Assessments for subscription {subscription_id} due to a transient error.",
            exc_info=True,
        )
        return []


def transform_assessments(assessments: list[dict]) -> list[dict]:
    """
    Transform the raw API response to the dictionary structure that the model expects.
    """
    transformed_assessments: list[dict[str, Any]] = []
    for assessment in assessments:
        transformed_assessment = {
            "id": assessment.get("id"),
            "name": assessment.get("name"),
            "display_name": assessment.get("display_name"),
            "description": assessment.get("properties", {})
            .get("metadata", {})
            .get("description"),
            "remediation_description": assessment.get("properties", {})
            .get("metadata", {})
            .get("remediation_description"),
        }
        transformed_assessments.append(transformed_assessment)
    return transformed_assessments


@timeit
def load_assessments(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    subscription_id: str,
    update_tag: int,
) -> None:
    """
    Load the transformed Azure Security Assessment data to Neo4j.
    """
    load(
        neo4j_session,
        AzureSecurityAssessmentSchema(),
        data,
        lastupdated=update_tag,
        AZURE_SUBSCRIPTION_ID=subscription_id,
    )


@timeit
def cleanup_assessments(
    neo4j_session: neo4j.Session, common_job_parameters: dict
) -> None:
    """
    Run the cleanup job for Azure Security Assessments.
    """
    GraphJob.from_node_schema(
        AzureSecurityAssessmentSchema(), common_job_parameters
    ).run(neo4j_session)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    credentials: Credentials,
    subscription_id: str,
    update_tag: int,
    common_job_parameters: dict,
) -> None:
    """
    The main sync function for Azure Security Center.
    """
    logger.info(
        f"Syncing Azure Security Center Assessments for subscription {subscription_id}."
    )
    client = SecurityCenter(credentials.credential, subscription_id)
    raw_assessments = get_assessments(client, subscription_id)
    transformed_assessments = transform_assessments(raw_assessments)
    load_assessments(
        neo4j_session, transformed_assessments, subscription_id, update_tag
    )
    cleanup_assessments(neo4j_session, common_job_parameters)
