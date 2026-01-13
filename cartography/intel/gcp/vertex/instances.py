import logging
from typing import Dict
from typing import List

import neo4j
from googleapiclient.discovery import Resource

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.gcp.vertex.instance import GCPVertexAIWorkbenchInstanceSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_workbench_api_locations(aiplatform: Resource, project_id: str) -> List[str]:
    """
    Gets all available Workbench (In Notebooks API) API locations for a project.
    The Notebooks API uses both zones and regions, unlike Vertex AI which primarily uses regions.
    Filters to commonly-used locations to improve sync performance.
    """
    import requests
    from google.auth.transport.requests import Request as AuthRequest

    # Get credentials and refresh token if needed
    creds = aiplatform._http.credentials
    if not creds.valid:
        creds.refresh(AuthRequest())

    # Query Notebooks API for available locations
    notebooks_endpoint = "https://notebooks.googleapis.com"
    url = f"{notebooks_endpoint}/v1/projects/{project_id}/locations"
    headers = {
        "Authorization": f"Bearer {creds.token}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()

        # Filter to commonly-used locations to avoid excessive API calls
        # Include major regions and their zones
        # Reference: https://cloud.google.com/vertex-ai/docs/general/locations
        supported_prefixes = {
            "us-central1",
            "us-east1",
            "us-east4",
            "us-west1",
            "us-west2",
            "us-west3",
            "us-west4",
            "europe-west1",
            "europe-west2",
            "europe-west3",
            "europe-west4",
            "asia-east1",
            "asia-northeast1",
            "asia-northeast3",
            "asia-southeast1",
            "australia-southeast1",
            "northamerica-northeast1",
            "southamerica-east1",
        }

        locations = []
        all_locations = data.get("locations", [])
        for location in all_locations:
            # Extract location ID from the full path
            # Format: "projects/PROJECT_ID/locations/LOCATION_ID"
            location_id = location.get("locationId", "")

            # Check if this location matches any of our supported prefixes
            # This handles both regions (us-central1) and zones (us-central1-a, us-central1-b)
            if any(location_id.startswith(prefix) for prefix in supported_prefixes):
                locations.append(location_id)

        logger.info(
            f"Found {len(locations)} supported Notebooks API locations "
            f"(filtered from {len(all_locations)} total) for project {project_id}"
        )
        return locations

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 403:
            logger.warning(
                f"Access forbidden when trying to get Notebooks API locations for project {project_id}. "
                "Ensure the Notebooks API is enabled and you have the necessary permissions.",
            )
        elif e.response.status_code == 404:
            logger.warning(
                f"Notebooks API locations not found for project {project_id}. "
                "The Notebooks API may not be enabled.",
            )
        else:
            logger.error(
                f"Error getting Notebooks API locations for project {project_id}: {e}",
                exc_info=True,
            )
        return []
    except Exception as e:
        logger.error(
            f"Unexpected error getting Notebooks API locations for project {project_id}: {e}",
            exc_info=True,
        )
        return []


@timeit
def get_workbench_instances_for_location(
    aiplatform: Resource,
    project_id: str,
    location: str,
) -> List[Dict]:
    """
    Gets all Vertex AI Workbench instances for a specific location.
    Note: This queries the Notebooks API v2 for Workbench instances. The v2 API is used
    by the GCP Console for creating new Workbench instances. The v1 API is deprecated.
    """
    from google.auth.transport.requests import Request as AuthRequest

    from cartography.intel.gcp.vertex.utils import paginate_vertex_api

    # Get credentials and refresh token if needed
    creds = aiplatform._http.credentials
    if not creds.valid:
        creds.refresh(AuthRequest())

    # Prepare request parameters for Notebooks API v2
    # Workbench Instances use notebooks.googleapis.com/v2, not aiplatform.googleapis.com
    notebooks_endpoint = "https://notebooks.googleapis.com"
    parent = f"projects/{project_id}/locations/{location}"
    headers = {
        "Authorization": f"Bearer {creds.token}",
        "Content-Type": "application/json",
    }
    url = f"{notebooks_endpoint}/v2/{parent}/instances"

    # Use helper function to handle pagination and error handling
    return paginate_vertex_api(
        url=url,
        headers=headers,
        resource_type="workbench instances",
        response_key="instances",
        location=location,
        project_id=project_id,
    )


@timeit
def transform_workbench_instances(instances: List[Dict]) -> List[Dict]:

    transformed_instances = []

    for instance in instances:
        # Extract service account from gceSetup.serviceAccounts
        # Workbench Instances store service account in gceSetup config
        service_account = None
        gce_setup = instance.get("gceSetup", {})
        service_accounts = gce_setup.get("serviceAccounts", [])
        if service_accounts and len(service_accounts) > 0:
            service_account = service_accounts[0].get("email")

        # Extract creator (v2 API uses 'creator' field instead of 'instanceOwners')
        # v1 API had instanceOwners array, v2 has a single creator string
        runtime_user = instance.get("creator")

        transformed_instance = {
            "id": instance.get("name"),  # Full resource name
            "name": instance.get("name"),
            "display_name": None,  # Instances don't have displayName
            "description": None,  # Instances don't have description
            "runtime_user": runtime_user,  # From creator field (v2 API)
            "notebook_runtime_type": None,  # Not applicable to Workbench Instances
            "create_time": instance.get("createTime"),
            "update_time": instance.get("updateTime"),
            "state": instance.get("state"),
            "health_state": instance.get("healthState"),
            "service_account": service_account,  # For USES_SERVICE_ACCOUNT relationship
        }

        transformed_instances.append(transformed_instance)

    logger.info(
        f"Transformed {len(transformed_instances)} Vertex AI Workbench instances"
    )
    return transformed_instances


@timeit
def load_workbench_instances(
    neo4j_session: neo4j.Session,
    instances: List[Dict],
    project_id: str,
    gcp_update_tag: int,
) -> None:

    load(
        neo4j_session,
        GCPVertexAIWorkbenchInstanceSchema(),
        instances,
        lastupdated=gcp_update_tag,
        PROJECT_ID=project_id,
    )


@timeit
def cleanup_workbench_instances(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict,
) -> None:

    GraphJob.from_node_schema(
        GCPVertexAIWorkbenchInstanceSchema(), common_job_parameters
    ).run(
        neo4j_session,
    )


@timeit
def sync_workbench_instances(
    neo4j_session: neo4j.Session,
    aiplatform: Resource,
    project_id: str,
    gcp_update_tag: int,
    common_job_parameters: Dict,
) -> None:

    logger.info("Syncing Vertex AI Workbench instances for project %s.", project_id)

    # Get all available locations for Notebooks API (includes both zones and regions)
    # Note: We use the Notebooks API location list, not Vertex AI locations, because
    # Workbench Instances can be deployed in zones (e.g., us-east1-b) not just regions
    locations = get_workbench_api_locations(aiplatform, project_id)

    # Collect instances from all locations
    all_instances = []
    for location in locations:
        instances = get_workbench_instances_for_location(
            aiplatform, project_id, location
        )
        all_instances.extend(instances)

    # Transform and load instances
    transformed_instances = transform_workbench_instances(all_instances)
    load_workbench_instances(
        neo4j_session, transformed_instances, project_id, gcp_update_tag
    )

    # Clean up stale data
    cleanup_workbench_instances(neo4j_session, common_job_parameters)
