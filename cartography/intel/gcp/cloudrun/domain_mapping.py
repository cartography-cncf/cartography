import logging
import re

import neo4j
from google.api_core.exceptions import PermissionDenied
from google.auth.exceptions import DefaultCredentialsError
from google.auth.exceptions import RefreshError
from googleapiclient.discovery import Resource

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.gcp.cloudrun.domain_mapping import (
    GCPCloudRunDomainMappingSchema,
)
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_domain_mappings(
    client: Resource, project_id: str, location: str = "-"
) -> list[dict]:
    """
    Gets GCP Cloud Run Domain Mappings for a project and location.

    :param client: The Cloud Run API client
    :param project_id: The GCP project ID
    :param location: The location to query. Use "-" to query all locations (default)
    :return: List of Cloud Run Domain Mapping dictionaries
    """
    domain_mappings: list[dict] = []
    try:
        parent = f"projects/{project_id}/locations/{location}"
        request = client.domainMappings().list(parent=parent)
        while request is not None:
            response = request.execute()
            domain_mappings.extend(response.get("domainMappings", []))
            request = client.domainMappings().list_next(
                previous_request=request,
                previous_response=response,
            )
        return domain_mappings
    except (PermissionDenied, DefaultCredentialsError, RefreshError) as e:
        logger.warning(
            f"Failed to get Cloud Run domain mappings for project {project_id} due to permissions or auth error: {e}",
        )
        raise


def transform_domain_mappings(
    domain_mappings_data: list[dict], project_id: str
) -> list[dict]:
    """
    Transforms the list of Cloud Run Domain Mapping dicts for ingestion.

    :param domain_mappings_data: Raw domain mapping data from the Cloud Run API
    :param project_id: The GCP project ID
    :return: Transformed list of domain mapping dictionaries
    """
    transformed: list[dict] = []
    for domain_mapping in domain_mappings_data:
        # Full resource name: projects/{project}/locations/{location}/domainMappings/{domain}
        full_name = domain_mapping.get("name", "")

        # The domain name is typically extracted from the resource name
        # Extract location and domain name from the full resource name
        name_match = re.match(
            r"projects/[^/]+/locations/([^/]+)/domainMappings/(.+)",
            full_name,
        )
        location = name_match.group(1) if name_match else None
        domain_name = name_match.group(2) if name_match else None

        # Get the route name - this is the service name that the domain points to
        # In Cloud Run v2 API, this is in spec.routeName
        spec = domain_mapping.get("spec", {})
        route_name_short = spec.get("routeName")

        # Construct the full service resource name
        route_name = None
        if location and route_name_short:
            route_name = f"projects/{project_id}/locations/{location}/services/{route_name_short}"

        transformed.append(
            {
                "id": full_name,
                "name": domain_name,
                "route_name": route_name,
                "project_id": project_id,
            },
        )
    return transformed


@timeit
def load_domain_mappings(
    neo4j_session: neo4j.Session,
    data: list[dict],
    project_id: str,
    update_tag: int,
) -> None:
    """
    Loads GCPCloudRunDomainMapping nodes and their relationships.

    :param neo4j_session: The Neo4j session
    :param data: Transformed domain mapping data
    :param project_id: The GCP project ID
    :param update_tag: Timestamp for tracking updates
    """
    load(
        neo4j_session,
        GCPCloudRunDomainMappingSchema(),
        data,
        lastupdated=update_tag,
        project_id=project_id,
    )


@timeit
def cleanup_domain_mappings(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict,
) -> None:
    """
    Cleans up stale Cloud Run domain mappings.

    :param neo4j_session: The Neo4j session
    :param common_job_parameters: Common job parameters for cleanup
    """
    GraphJob.from_node_schema(
        GCPCloudRunDomainMappingSchema(), common_job_parameters
    ).run(
        neo4j_session,
    )


@timeit
def sync_domain_mappings(
    neo4j_session: neo4j.Session,
    client: Resource,
    project_id: str,
    update_tag: int,
    common_job_parameters: dict,
) -> None:
    """
    Syncs GCP Cloud Run Domain Mappings for a project.

    :param neo4j_session: The Neo4j session
    :param client: The Cloud Run API client
    :param project_id: The GCP project ID
    :param update_tag: Timestamp for tracking updates
    :param common_job_parameters: Common job parameters for cleanup
    """
    logger.info(f"Syncing Cloud Run Domain Mappings for project {project_id}.")
    domain_mappings_raw = get_domain_mappings(client, project_id)
    if not domain_mappings_raw:
        logger.info(f"No Cloud Run domain mappings found for project {project_id}.")

    domain_mappings = transform_domain_mappings(domain_mappings_raw, project_id)
    load_domain_mappings(neo4j_session, domain_mappings, project_id, update_tag)

    cleanup_job_params = common_job_parameters.copy()
    cleanup_job_params["project_id"] = project_id
    cleanup_domain_mappings(neo4j_session, cleanup_job_params)
