# Google Compute Engine Network Endpoint Groups
# https://cloud.google.com/compute/docs/reference/rest/v1/networkEndpointGroups
from __future__ import annotations

import logging

import neo4j
from googleapiclient.discovery import Resource
from googleapiclient.errors import HttpError

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.gcp.util import aggregated_response_cleanup_safe
from cartography.intel.gcp.util import classify_gcp_http_error
from cartography.intel.gcp.util import gcp_api_execute_with_retry
from cartography.intel.gcp.util import GCP_EXPECTED_SKIP_CATEGORIES
from cartography.intel.gcp.util import merge_aggregated_scope_items
from cartography.intel.gcp.util import parse_compute_full_uri_to_partial_uri
from cartography.intel.gcp.util import summarize_gcp_http_error
from cartography.intel.gcp.util import with_return_partial_success
from cartography.models.gcp.compute.network_endpoint_group import (
    GCPNetworkEndpointGroupSchema,
)
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_gcp_network_endpoint_groups(
    project_id: str,
    compute: Resource,
) -> Resource | None:
    """
    Return all zonal, regional and global network endpoint groups in the given project.
    :param project_id: The project ID
    :param compute: The compute resource object created by googleapiclient.discovery.build()
    :return: Aggregated response object containing NEGs, or None if access is denied
    """
    items: dict[str, dict] = {}
    response_id = f"projects/{project_id}/aggregated/networkEndpointGroups"
    req = with_return_partial_success(
        compute.networkEndpointGroups().aggregatedList(project=project_id),
    )
    while req is not None:
        try:
            res = gcp_api_execute_with_retry(req)
        except HttpError as e:
            if classify_gcp_http_error(e) in GCP_EXPECTED_SKIP_CATEGORIES:
                logger.warning(
                    "GCP: Unable to list network endpoint groups for project %s; skipping this collector. %s",
                    project_id,
                    summarize_gcp_http_error(e),
                )
                return None
            raise
        merge_aggregated_scope_items(items, res, "networkEndpointGroups")
        response_id = res.get("id", response_id)
        req = compute.networkEndpointGroups().aggregatedList_next(
            previous_request=req,
            previous_response=res,
        )
    return {"id": response_id, "items": items}


@timeit
def transform_gcp_network_endpoint_groups(
    response: Resource,
    project_id: str,
) -> list[dict]:
    """
    Transform the NEG aggregated response object for Neo4j ingestion.
    :param response: The response object returned from networkEndpointGroups.aggregatedList()
    :param project_id: The GCP project ID
    :return: List of transformed NEG dicts ready for loading
    """
    neg_list: list[dict] = []
    for scope, scoped_list in response.get("items", {}).items():
        for neg in scoped_list.get("networkEndpointGroups", []):
            zone = neg.get("zone")
            region = neg.get("region")
            neg_list.append(
                {
                    # Same form as the backends[].group URLs a backend service points at.
                    "partial_uri": f"projects/{project_id}/{scope}/networkEndpointGroups/{neg['name']}",
                    "project_id": project_id,
                    "name": neg.get("name"),
                    "self_link": neg.get("selfLink"),
                    "zone": zone.split("/")[-1] if zone else None,
                    "region": region.split("/")[-1] if region else None,
                    "description": neg.get("description"),
                    "network_endpoint_type": neg.get("networkEndpointType"),
                    "network_partial_uri": parse_compute_full_uri_to_partial_uri(
                        neg.get("network")
                    ),
                    "subnetwork_partial_uri": parse_compute_full_uri_to_partial_uri(
                        neg.get("subnetwork")
                    ),
                    "default_port": neg.get("defaultPort"),
                    "size": neg.get("size"),
                    "creation_timestamp": neg.get("creationTimestamp"),
                }
            )
    return neg_list


@timeit
def load_gcp_network_endpoint_groups(
    neo4j_session: neo4j.Session,
    negs: list[dict],
    gcp_update_tag: int,
    project_id: str,
) -> None:
    load(
        neo4j_session,
        GCPNetworkEndpointGroupSchema(),
        negs,
        lastupdated=gcp_update_tag,
        PROJECT_ID=project_id,
    )


@timeit
def cleanup_gcp_network_endpoint_groups(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict,
) -> None:
    GraphJob.from_node_schema(
        GCPNetworkEndpointGroupSchema(), common_job_parameters
    ).run(neo4j_session)


@timeit
def sync_gcp_network_endpoint_groups(
    neo4j_session: neo4j.Session,
    compute: Resource,
    project_id: str,
    gcp_update_tag: int,
    common_job_parameters: dict,
) -> None:
    logger.info("Syncing GCP network endpoint groups for project %s", project_id)
    response = get_gcp_network_endpoint_groups(project_id, compute)
    if response is None:
        return
    negs = transform_gcp_network_endpoint_groups(response, project_id)
    load_gcp_network_endpoint_groups(neo4j_session, negs, gcp_update_tag, project_id)

    if aggregated_response_cleanup_safe(response):
        cleanup_gcp_network_endpoint_groups(neo4j_session, common_job_parameters)
