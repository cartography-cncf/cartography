# Google Compute Engine Target SSL Proxies
# https://cloud.google.com/compute/docs/reference/rest/v1/targetSslProxies
from __future__ import annotations

import logging
from typing import Any

import neo4j
from googleapiclient.discovery import Resource
from googleapiclient.errors import HttpError

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.gcp.util import classify_gcp_http_error
from cartography.intel.gcp.util import gcp_api_execute_with_retry
from cartography.intel.gcp.util import GCP_EXPECTED_SKIP_CATEGORIES
from cartography.intel.gcp.util import parse_compute_full_uri_to_partial_uri
from cartography.intel.gcp.util import summarize_gcp_http_error
from cartography.models.gcp.compute.target_ssl_proxy import GCPTargetSslProxySchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_gcp_target_ssl_proxies(
    project_id: str,
    compute: Resource,
) -> Resource | None:
    """
    Return list of all target SSL proxies in the given project.
    :param project_id: The project ID
    :param compute: The compute resource object created by googleapiclient.discovery.build()
    :return: Response object containing data on all target SSL proxies for a given project, or None if access is denied
    """
    items: list[dict] = []
    response_id = f"projects/{project_id}/global/targetSslProxies"
    req = compute.targetSslProxies().list(project=project_id)
    while req is not None:
        try:
            res = gcp_api_execute_with_retry(req)
        except HttpError as e:
            if classify_gcp_http_error(e) in GCP_EXPECTED_SKIP_CATEGORIES:
                logger.warning(
                    "GCP: Unable to list target SSL proxies for project %s; skipping this collector. %s",
                    project_id,
                    summarize_gcp_http_error(e),
                )
                return None
            raise
        items.extend(res.get("items", []))
        response_id = res.get("id", response_id)
        req = compute.targetSslProxies().list_next(
            previous_request=req, previous_response=res
        )
    return {"id": response_id, "items": items}


@timeit
def transform_gcp_target_ssl_proxies(response: Resource, project_id: str) -> list[dict]:
    """
    Transform the target SSL proxy response object for Neo4j ingestion.
    :param response: The response object returned from targetSslProxies.list()
    :param project_id: The GCP project ID
    :return: List of transformed proxy dicts ready for loading
    """
    proxy_list: list[dict] = []
    prefix = response["id"]

    for proxy in response.get("items", []):
        transformed: dict[str, Any] = {}

        partial_uri = f"{prefix}/{proxy['name']}"
        transformed["partial_uri"] = partial_uri
        transformed["project_id"] = project_id
        transformed["name"] = proxy.get("name")
        transformed["self_link"] = proxy.get("selfLink")
        transformed["description"] = proxy.get("description")
        transformed["service_partial_uri"] = parse_compute_full_uri_to_partial_uri(
            proxy.get("service")
        )
        transformed["ssl_policy_partial_uri"] = parse_compute_full_uri_to_partial_uri(
            proxy.get("sslPolicy")
        )
        transformed["creation_timestamp"] = proxy.get("creationTimestamp")

        proxy_list.append(transformed)
    return proxy_list


@timeit
def load_gcp_target_ssl_proxies(
    neo4j_session: neo4j.Session,
    proxies: list[dict],
    gcp_update_tag: int,
    project_id: str,
) -> None:
    """
    Ingest GCP target SSL proxy data to Neo4j.
    """
    load(
        neo4j_session,
        GCPTargetSslProxySchema(),
        proxies,
        lastupdated=gcp_update_tag,
        PROJECT_ID=project_id,
    )


@timeit
def cleanup_gcp_target_ssl_proxies(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict,
) -> None:
    """
    Delete out-of-date GCP target SSL proxies and relationships.
    """
    GraphJob.from_node_schema(GCPTargetSslProxySchema(), common_job_parameters).run(
        neo4j_session,
    )


@timeit
def sync_gcp_target_ssl_proxies(
    neo4j_session: neo4j.Session,
    compute: Resource,
    project_id: str,
    gcp_update_tag: int,
    common_job_parameters: dict,
) -> None:
    """
    Sync GCP target SSL proxies, ingest to Neo4j, and clean up old data.
    """
    logger.info("Syncing GCP target SSL proxies for project %s", project_id)
    response = get_gcp_target_ssl_proxies(project_id, compute)
    if response is None:
        return
    proxies = transform_gcp_target_ssl_proxies(response, project_id)
    load_gcp_target_ssl_proxies(neo4j_session, proxies, gcp_update_tag, project_id)
    cleanup_gcp_target_ssl_proxies(neo4j_session, common_job_parameters)
