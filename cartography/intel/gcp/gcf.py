import json
import logging
from typing import Any

import neo4j
from googleapiclient.discovery import Resource
from googleapiclient.errors import HttpError

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.gcp.util import gcp_api_execute_with_retry
from cartography.models.gcp.gcf import GCPCloudFunctionSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_gcp_cloud_functions(
    project_id: str, functions_client: Resource
) -> list[dict[str, Any]] | None:
    """
    Fetches raw GCP Cloud Functions data for a given project.

    Returns:
        list[dict[str, Any]]: List of cloud functions (empty list if project has no functions)
        None: If API access is denied or API is not enabled (to signal that sync should be skipped)
    """
    logger.info(f"Collecting Cloud Functions for project: {project_id}")
    collected_functions: list[dict[str, Any]] = []
    try:
        parent = f"projects/{project_id}/locations/-"
        request = (
            functions_client.projects().locations().functions().list(parent=parent)
        )
        while request is not None:
            response = gcp_api_execute_with_retry(request)
            if "functions" in response:
                collected_functions.extend(response["functions"])
            request = (
                functions_client.projects()
                .locations()
                .functions()
                .list_next(
                    previous_request=request,
                    previous_response=response,
                )
            )
        return collected_functions
    except HttpError as e:
        error_json = json.loads(e.content.decode("utf-8"))
        err = error_json.get("error", {})
        if err.get("status", "") == "PERMISSION_DENIED" or (
            err.get("message") and "API has not been used" in err.get("message")
        ):
            logger.warning(
                "Could not retrieve Cloud Functions on project %s due to permissions "
                "issues or API not enabled. Code: %s, Message: %s. Skipping sync to preserve existing data.",
                project_id,
                err.get("code"),
                err.get("message"),
            )
            return None
        else:
            raise


def _parse_region_from_name(name: str) -> str:
    """
    Helper function to safely parse the region from a function's full name string.
    """
    try:
        # Full name is projects/{project}/locations/{region}/functions/{function-name}
        return name.split("/")[3]
    except IndexError:
        logger.warning(f"Could not parse region from function name: {name}")
        # Default to global if region can't be parsed
        return "global"


@timeit
def transform_gcp_cloud_functions(
    functions: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    """
    Transforms the raw function data to flatten triggers and group the data by region.
    """
    transformed_and_grouped_by_region: dict[str, list[dict[str, Any]]] = {}
    for func_data in functions:
        # Flatten nested data
        func_data["https_trigger_url"] = func_data.get("httpsTrigger", {}).get("url")
        func_data["event_trigger_type"] = func_data.get("eventTrigger", {}).get(
            "eventType"
        )
        func_data["event_trigger_resource"] = func_data.get("eventTrigger", {}).get(
            "resource"
        )

        # Parse the region and group the function data
        region = _parse_region_from_name(func_data.get("name", ""))
        if region not in transformed_and_grouped_by_region:
            transformed_and_grouped_by_region[region] = []
        transformed_and_grouped_by_region[region].append(func_data)

    return transformed_and_grouped_by_region


@timeit
def load_gcp_cloud_functions(
    neo4j_session: neo4j.Session,
    data: dict[str, list[dict[str, Any]]],
    project_id: str,
    update_tag: int,
) -> None:
    """
    Ingests transformed and grouped GCP Cloud Functions using the Cartography data model.
    """
    for region, functions_in_region in data.items():
        logger.info(
            "Loading %d GCP Cloud Functions for project %s in region %s.",
            len(functions_in_region),
            project_id,
            region,
        )
        load(
            neo4j_session,
            GCPCloudFunctionSchema(),
            functions_in_region,
            lastupdated=update_tag,
            projectId=project_id,
            region=region,
        )


@timeit
def cleanup_gcp_cloud_functions(
    neo4j_session: neo4j.Session,
    cleanup_job_params: dict[str, Any],
) -> None:
    """
    Deletes stale GCPCloudFunction nodes and their relationships.
    """
    cleanup_job = GraphJob.from_node_schema(
        GCPCloudFunctionSchema(), cleanup_job_params
    )
    cleanup_job.run(neo4j_session)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    functions_client: Resource,
    project_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    The main orchestration function to get, transform, load, and clean up GCP Cloud Functions.
    """
    logger.info(f"Syncing GCP Cloud Functions for project {project_id}.")

    functions_data = get_gcp_cloud_functions(project_id, functions_client)

    # Only load and cleanup if we successfully retrieved data (even if empty list of functions)
    # If get() returned None due to permission/API errors, we skip both load and cleanup
    # to avoid deleting previously ingested data
    if functions_data is not None:
        if functions_data:
            transformed_functions = transform_gcp_cloud_functions(functions_data)
            load_gcp_cloud_functions(
                neo4j_session, transformed_functions, project_id, update_tag
            )

        cleanup_job_params = common_job_parameters.copy()
        cleanup_job_params["projectId"] = project_id
        cleanup_gcp_cloud_functions(neo4j_session, cleanup_job_params)
