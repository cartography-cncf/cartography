# Google Compute Engine Backend Service
# https://cloud.google.com/compute/docs/reference/rest/v1/backendServices
# https://cloud.google.com/compute/docs/reference/rest/v1/regionBackendServices
from __future__ import annotations

import logging
from typing import Any

import neo4j
from googleapiclient.discovery import Resource
from googleapiclient.errors import HttpError

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.gcp.util import gcp_api_execute_with_retry
from cartography.intel.gcp.util import get_error_reason
from cartography.intel.gcp.util import parse_compute_full_uri_to_partial_uri
from cartography.models.gcp.compute.backend_service import GCPBackendServiceSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_gcp_global_backend_services(
    project_id: str,
    compute: Resource,
) -> Resource:
    """
    Return list of all global backend services in the given project.
    :param project_id: The project ID
    :param compute: The compute resource object created by googleapiclient.discovery.build()
    :return: Response object containing data on all global backend services for a given project
    """
    items: list[dict] = []
    response_id = f"projects/{project_id}/global/backendServices"
    req = compute.backendServices().list(project=project_id)
    while req is not None:
        res = gcp_api_execute_with_retry(req)
        items.extend(res.get("items", []))
        response_id = res.get("id", response_id)
        req = compute.backendServices().list_next(
            previous_request=req, previous_response=res
        )
    return {"id": response_id, "items": items}


@timeit
def get_gcp_regional_backend_services(
    project_id: str,
    region: str,
    compute: Resource,
) -> Resource | None:
    """
    Return list of all regional backend services in the given project and region.
    Returns None if the region is invalid.
    :param project_id: The project ID
    :param region: The region to pull backend services from
    :param compute: The compute resource object created by googleapiclient.discovery.build()
    :return: Response object containing backend services for a given project and region, or None if region is invalid
    """
    items: list[dict] = []
    response_id = f"projects/{project_id}/regions/{region}/backendServices"
    req = compute.regionBackendServices().list(project=project_id, region=region)
    while req is not None:
        try:
            res = gcp_api_execute_with_retry(req)
        except HttpError as e:
            reason = get_error_reason(e)
            if reason == "invalid":
                logger.warning(
                    "GCP: Invalid region %s for project %s; skipping backend services sync for this region.",
                    region,
                    project_id,
                )
                return None
            raise
        items.extend(res.get("items", []))
        response_id = res.get("id", response_id)
        req = compute.regionBackendServices().list_next(
            previous_request=req, previous_response=res
        )
    return {"id": response_id, "items": items}


@timeit
def transform_gcp_backend_services(response: Resource, project_id: str) -> list[dict]:
    """
    Transform the backend service response object for Neo4j ingestion.
    :param response: The response object returned from backendServices.list() or regionBackendServices.list()
    :param project_id: The GCP project ID
    :return: List of transformed backend service dicts ready for loading
    """
    backend_service_list: list[dict] = []
    prefix = response["id"]

    for bs in response.get("items", []):
        backend_service: dict[str, Any] = {}

        partial_uri = f"{prefix}/{bs['name']}"
        backend_service["partial_uri"] = partial_uri
        backend_service["project_id"] = project_id
        backend_service["name"] = bs.get("name")
        backend_service["self_link"] = bs.get("selfLink")
        backend_service["description"] = bs.get("description")
        backend_service["load_balancing_scheme"] = bs.get("loadBalancingScheme")
        backend_service["protocol"] = bs.get("protocol")
        backend_service["port"] = bs.get("port")
        backend_service["port_name"] = bs.get("portName")
        backend_service["timeout_sec"] = bs.get("timeoutSec")
        security_policy = bs.get("securityPolicy")
        backend_service["security_policy"] = security_policy
        backend_service["security_policy_partial_uri"] = (
            parse_compute_full_uri_to_partial_uri(security_policy)
        )
        backend_service["creation_timestamp"] = bs.get("creationTimestamp")

        region = bs.get("region")
        backend_service["region"] = region.split("/")[-1] if region else None

        # Extract instance group partial URIs from backends[].group for HAS_BACKEND rel
        backend_groups = bs.get("backends", [])
        backend_service["backend_group_partial_uris"] = [
            parse_compute_full_uri_to_partial_uri(group_url)
            for b in backend_groups
            if (group_url := b.get("group"))
        ]

        backend_service_list.append(backend_service)
    return backend_service_list


@timeit
def load_gcp_backend_services(
    neo4j_session: neo4j.Session,
    backend_services: list[dict],
    gcp_update_tag: int,
    project_id: str,
) -> None:
    """
    Ingest GCP backend service data to Neo4j.
    :param neo4j_session: The Neo4j session
    :param backend_services: List of transformed backend service dicts
    :param gcp_update_tag: The timestamp to set these Neo4j nodes with
    :param project_id: The GCP project ID
    :return: Nothing
    """
    load(
        neo4j_session,
        GCPBackendServiceSchema(),
        backend_services,
        lastupdated=gcp_update_tag,
        PROJECT_ID=project_id,
    )


@timeit
def cleanup_gcp_backend_services(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict,
) -> None:
    """
    Delete out-of-date GCP backend services and relationships.
    :param neo4j_session: The Neo4j session
    :param common_job_parameters: dict of other job parameters to pass to Neo4j
    :return: Nothing
    """
    GraphJob.from_node_schema(GCPBackendServiceSchema(), common_job_parameters).run(
        neo4j_session,
    )


@timeit
def sync_gcp_backend_services(
    neo4j_session: neo4j.Session,
    compute: Resource,
    project_id: str,
    regions: list[str],
    gcp_update_tag: int,
    common_job_parameters: dict,
) -> None:
    """
    Sync GCP global and regional backend services, ingest to Neo4j, and clean up old data.
    :param neo4j_session: The Neo4j session
    :param compute: The GCP Compute resource object
    :param project_id: The project ID to sync
    :param regions: List of regions
    :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with
    :param common_job_parameters: dict of other job parameters to pass to Neo4j
    :return: Nothing
    """
    logger.info("Syncing GCP backend services for project %s", project_id)

    # Global backend services
    global_response = get_gcp_global_backend_services(project_id, compute)
    backend_services = transform_gcp_backend_services(global_response, project_id)
    load_gcp_backend_services(
        neo4j_session, backend_services, gcp_update_tag, project_id
    )

    # Regional backend services
    for r in regions:
        regional_response = get_gcp_regional_backend_services(project_id, r, compute)
        if regional_response is None:
            continue
        backend_services = transform_gcp_backend_services(regional_response, project_id)
        load_gcp_backend_services(
            neo4j_session, backend_services, gcp_update_tag, project_id
        )

    # Cleanup after all loads complete
    cleanup_gcp_backend_services(neo4j_session, common_job_parameters)
