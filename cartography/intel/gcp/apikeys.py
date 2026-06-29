import json
import logging
from typing import Dict
from typing import List

import neo4j
from dateutil import parser as dateutil_parser
from googleapiclient.discovery import HttpError
from googleapiclient.discovery import Resource

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.gcp.util import classify_gcp_http_error
from cartography.intel.gcp.util import gcp_api_execute_with_retry
from cartography.intel.gcp.util import is_permission_denied_error
from cartography.intel.gcp.util import summarize_gcp_http_error
from cartography.models.gcp.apikeys import GCPApiKeySchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_api_keys(apikeys: Resource, project_id: str) -> List[Dict]:
    """
    Get all API Keys (apikeys.googleapis.com) for a given project. Keys are a
    global resource, so we list them under the "global" location.
    """
    try:
        keys: List[Dict] = []
        parent = f"projects/{project_id}/locations/global"
        req = apikeys.projects().locations().keys().list(parent=parent)
        while req is not None:
            res = gcp_api_execute_with_retry(req)
            keys.extend(res.get("keys", []))
            req = (
                apikeys.projects()
                .locations()
                .keys()
                .list_next(
                    previous_request=req,
                    previous_response=res,
                )
            )
        return keys
    except HttpError as e:
        category = classify_gcp_http_error(e)
        if category == "invalid":
            logger.warning(
                "The project %s is invalid - returned a 400 invalid error. %s",
                project_id,
                summarize_gcp_http_error(e),
            )
            return []
        elif is_permission_denied_error(e):
            logger.warning(
                "You do not have apikeys.keys.list access to the project %s. %s",
                project_id,
                summarize_gcp_http_error(e),
            )
            return []
        elif category == "billing_disabled":
            logger.warning(
                "Billing is disabled for project %s. "
                "Skipping API Keys sync for this project. %s",
                project_id,
                summarize_gcp_http_error(e),
            )
            return []
        elif category == "api_disabled":
            logger.info(
                "API Keys API appears disabled for project %s. "
                "Skipping API Keys sync for this project. %s",
                project_id,
                summarize_gcp_http_error(e),
            )
            return []
        else:
            raise


def transform_api_keys(keys: List[Dict]) -> List[Dict]:
    """
    Transform GCP API Keys to match the data model.
    """
    transformed = []
    for key in keys:
        restrictions = key.get("restrictions")
        transformed.append(
            {
                "id": key["name"],
                "uid": key.get("uid"),
                "name": key["name"],
                "displayName": key.get("displayName"),
                "createTime": _parse_dt(key.get("createTime")),
                "updateTime": _parse_dt(key.get("updateTime")),
                "deleteTime": _parse_dt(key.get("deleteTime")),
                "restricted": bool(restrictions),
                "restrictions": json.dumps(restrictions) if restrictions else None,
                "etag": key.get("etag"),
            }
        )
    return transformed


def _parse_dt(value: str | None) -> object | None:
    # API Keys timestamps are RFC3339 strings; store as native datetimes.
    return dateutil_parser.isoparse(value) if value else None


@timeit
def load_api_keys(
    neo4j_session: neo4j.Session,
    keys: List[Dict],
    project_id: str,
    gcp_update_tag: int,
) -> None:
    load(
        neo4j_session,
        GCPApiKeySchema(),
        keys,
        lastupdated=gcp_update_tag,
        PROJECT_ID=project_id,
    )


@timeit
def cleanup_api_keys(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict,
) -> None:
    logger.debug("Running GCP API Keys cleanup job.")
    GraphJob.from_node_schema(
        GCPApiKeySchema(),
        common_job_parameters,
    ).run(neo4j_session)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    apikeys: Resource,
    project_id: str,
    gcp_update_tag: int,
    common_job_parameters: Dict,
) -> None:
    """
    Sync GCP API Keys (apikeys.googleapis.com) for a project.
    """
    logger.info("Syncing API Keys for project %s.", project_id)
    keys = get_api_keys(apikeys, project_id)
    transformed = transform_api_keys(keys)
    load_api_keys(neo4j_session, transformed, project_id, gcp_update_tag)
    cleanup_api_keys(neo4j_session, common_job_parameters)
