import logging
import json
from typing import Dict, List
from itertools import groupby
from operator import itemgetter

import neo4j
from googleapiclient.discovery import Resource
from googleapiclient.errors import HttpError

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.gcp.gcf import GCPCloudFunctionSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_gcp_cloud_functions(project_id: str, functions_client: Resource) -> List[Dict]:
    """
    Fetches raw GCP Cloud Functions data for a given project across all available locations.
    """
    logger.info(f"Collecting Cloud Functions for project: {project_id}")
    collected_functions = []
    try:
        parent = f"projects/{project_id}/locations/-"
        request = functions_client.projects().locations().functions().list(parent=parent)
        while request is not None:
            response = request.execute()
            if 'functions' in response:
                collected_functions.extend(response['functions'])
            request = functions_client.projects().locations().functions().list_next(
                previous_request=request,
                previous_response=response,
            )
        return collected_functions
    except HttpError as e:
        error_json = json.loads(e.content.decode("utf-8"))
        err = error_json.get("error", {})
        if (
            err.get("status", "") == "PERMISSION_DENIED"
            or (err.get("message") and "API has not been used" in err.get("message"))
        ):
            logger.warning(
                (
                    "Could not retrieve Cloud Functions on project %s due to permissions issues or API not enabled. Code: %s, Message: %s"
                ),
                project_id,
                err.get("code"),
                err.get("message"),
            )
            return []
        else:
            raise


@timeit
def load_gcp_cloud_functions(
    neo4j_session: neo4j.Session,
    data: List[Dict],
    project_id: str,
    update_tag: int,
) -> None:
    """
    Ingests GCP Cloud Functions using the Cartography data model.
    """
    logger.info(f"Loading {len(data)} GCP Cloud Functions for project {project_id}.")

    transformed_data = []
    for func_data in data:
        func_data['https_trigger_url'] = func_data.get('httpsTrigger', {}).get('url')
        func_data['event_trigger_type'] = func_data.get('eventTrigger', {}).get('eventType')
        func_data['event_trigger_resource'] = func_data.get('eventTrigger', {}).get('resource')
        transformed_data.append(func_data)

    transformed_data.sort(key=lambda x: x['name'].split('/')[3] if len(x['name'].split('/')) > 3 else None)
    for region, functions_in_region in groupby(transformed_data, key=lambda x: x['name'].split('/')[3] if len(x['name'].split('/')) > 3 else None):
        if region:
            functions_list = list(functions_in_region)
           
            load(
                neo4j_session,
                GCPCloudFunctionSchema(),
                functions_list,
                lastupdated=update_tag,
                projectId=project_id, 
                region=region,
            )


@timeit
def cleanup_gcp_cloud_functions(neo4j_session: neo4j.Session, cleanup_job_params: Dict) -> None:
    """
    Deletes stale GCPCloudFunction nodes and their relationships.
    """
    cleanup_job = GraphJob.from_node_schema(GCPCloudFunctionSchema(), cleanup_job_params)
    cleanup_job.run(neo4j_session)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    functions_client: Resource,
    project_id: str,
    update_tag: int,
    common_job_parameters: Dict,
) -> None:
    """
    The main orchestration function to get, transform, load, and clean up GCP Cloud Functions.
    """
    logger.info(f"Syncing GCP Cloud Functions for project {project_id}.")

    functions_data = get_gcp_cloud_functions(project_id, functions_client)
    if functions_data:
        # The load function now handles the transformation
        load_gcp_cloud_functions(neo4j_session, functions_data, project_id, update_tag)

    cleanup_job_params = common_job_parameters.copy()
    cleanup_job_params["projectId"] = project_id
    cleanup_gcp_cloud_functions(neo4j_session, cleanup_job_params)