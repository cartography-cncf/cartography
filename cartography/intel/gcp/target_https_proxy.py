# Google Compute Engine Target HTTPS Proxies
# https://cloud.google.com/compute/docs/reference/rest/v1/targetHttpsProxies
from __future__ import annotations

import logging
from typing import Any

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
from cartography.models.gcp.compute.target_https_proxy import GCPTargetHttpsProxySchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_gcp_target_https_proxies(
    project_id: str,
    compute: Resource,
) -> Resource | None:
    """
    Return all global and regional target HTTPS proxies in the given project.
    :param project_id: The project ID
    :param compute: The compute resource object created by googleapiclient.discovery.build()
    :return: Aggregated response object containing target HTTPS proxies, or None if access is denied
    """
    items: dict[str, dict] = {}
    response_id = f"projects/{project_id}/aggregated/targetHttpsProxies"
    req = compute.targetHttpsProxies().aggregatedList(
        project=project_id,
        returnPartialSuccess=True,
    )
    while req is not None:
        try:
            res = gcp_api_execute_with_retry(req)
        except HttpError as e:
            if classify_gcp_http_error(e) in GCP_EXPECTED_SKIP_CATEGORIES:
                logger.warning(
                    "GCP: Unable to list target HTTPS proxies for project %s; skipping this collector. %s",
                    project_id,
                    summarize_gcp_http_error(e),
                )
                return None
            raise
        merge_aggregated_scope_items(items, res, "targetHttpsProxies")
        response_id = res.get("id", response_id)
        req = compute.targetHttpsProxies().aggregatedList_next(
            previous_request=req,
            previous_response=res,
        )
    return {"id": response_id, "items": items}


def _transform_gcp_target_https_proxy(
    proxy: dict[str, Any],
    project_id: str,
    scope: str,
) -> dict[str, Any]:
    partial_uri = f"projects/{project_id}/{scope}/targetHttpsProxies/{proxy['name']}"
    transformed: dict[str, Any] = {}
    transformed["partial_uri"] = partial_uri
    transformed["project_id"] = project_id
    transformed["region"] = None if scope == "global" else scope.split("regions/")[-1]
    transformed["name"] = proxy.get("name")
    transformed["self_link"] = proxy.get("selfLink")
    transformed["description"] = proxy.get("description")
    transformed["url_map_partial_uri"] = parse_compute_full_uri_to_partial_uri(
        proxy.get("urlMap")
    )
    transformed["ssl_policy_partial_uri"] = parse_compute_full_uri_to_partial_uri(
        proxy.get("sslPolicy")
    )
    transformed["creation_timestamp"] = proxy.get("creationTimestamp")
    return transformed


@timeit
def transform_gcp_target_https_proxies(
    response: Resource, project_id: str
) -> list[dict]:
    """
    Transform the target HTTPS proxy response object for Neo4j ingestion.
    :param response: The response object returned from targetHttpsProxies.aggregatedList()
    :param project_id: The GCP project ID
    :return: List of transformed proxy dicts ready for loading
    """
    proxy_list: list[dict] = []

    for scope, scoped_list in response.get("items", {}).items():
        for proxy in scoped_list.get("targetHttpsProxies", []):
            proxy_list.append(
                _transform_gcp_target_https_proxy(proxy, project_id, scope)
            )
    return proxy_list


@timeit
def load_gcp_target_https_proxies(
    neo4j_session: neo4j.Session,
    proxies: list[dict],
    gcp_update_tag: int,
    project_id: str,
) -> None:
    """
    Ingest GCP target HTTPS proxy data to Neo4j.
    """
    load(
        neo4j_session,
        GCPTargetHttpsProxySchema(),
        proxies,
        lastupdated=gcp_update_tag,
        PROJECT_ID=project_id,
    )


@timeit
def cleanup_gcp_target_https_proxies(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict,
) -> None:
    """
    Delete out-of-date GCP target HTTPS proxies and relationships.
    """
    GraphJob.from_node_schema(GCPTargetHttpsProxySchema(), common_job_parameters).run(
        neo4j_session,
    )


@timeit
def sync_gcp_target_https_proxies(
    neo4j_session: neo4j.Session,
    compute: Resource,
    project_id: str,
    gcp_update_tag: int,
    common_job_parameters: dict,
) -> None:
    """
    Sync GCP global and regional target HTTPS proxies, ingest to Neo4j, and clean up old data.
    """
    logger.info("Syncing GCP target HTTPS proxies for project %s", project_id)
    response = get_gcp_target_https_proxies(project_id, compute)
    if response is None:
        return
    proxies = transform_gcp_target_https_proxies(response, project_id)
    load_gcp_target_https_proxies(neo4j_session, proxies, gcp_update_tag, project_id)

    if aggregated_response_cleanup_safe(response):
        cleanup_gcp_target_https_proxies(neo4j_session, common_job_parameters)
