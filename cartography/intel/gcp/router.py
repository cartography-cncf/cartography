# Google Compute Engine Cloud Routers and Cloud NAT configs
# https://cloud.google.com/compute/docs/reference/rest/v1/routers
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
from cartography.intel.gcp.util import merge_aggregated_scope_items
from cartography.intel.gcp.util import parse_compute_full_uri_to_partial_uri
from cartography.intel.gcp.util import summarize_gcp_http_error
from cartography.models.gcp.compute.cloud_nat import GCPCloudNatSchema
from cartography.models.gcp.compute.router import GCPRouterSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

_EXPECTED_SKIP_CATEGORIES = ("api_disabled", "billing_disabled", "forbidden")


@timeit
def get_gcp_routers(
    project_id: str,
    compute: Resource,
) -> Resource | None:
    """
    Return all Cloud Routers in the given project.
    :param project_id: The project ID
    :param compute: The compute resource object created by googleapiclient.discovery.build()
    :return: Aggregated response object containing Cloud Routers, or None if access is denied
    """
    items: dict[str, dict] = {}
    response_id = f"projects/{project_id}/aggregated/routers"
    req = compute.routers().aggregatedList(
        project=project_id,
        returnPartialSuccess=True,
    )
    while req is not None:
        try:
            res = gcp_api_execute_with_retry(req)
        except HttpError as e:
            if classify_gcp_http_error(e) in _EXPECTED_SKIP_CATEGORIES:
                logger.warning(
                    "GCP: Unable to list Cloud Routers for project %s; skipping this collector. %s",
                    project_id,
                    summarize_gcp_http_error(e),
                )
                return None
            raise
        merge_aggregated_scope_items(items, res, "routers")
        response_id = res.get("id", response_id)
        req = compute.routers().aggregatedList_next(
            previous_request=req,
            previous_response=res,
        )
    return {"id": response_id, "items": items}


def _scope_to_region(scope: str) -> str | None:
    if scope == "global":
        return None
    return scope.split("regions/")[-1]


@timeit
def transform_gcp_routers(
    response: Resource,
    project_id: str,
) -> tuple[list[dict], list[dict]]:
    """
    Transform Cloud Router aggregatedList response into router and Cloud NAT rows.
    :param response: The response object returned from routers.aggregatedList()
    :param project_id: The GCP project ID
    :return: Tuple of router rows and Cloud NAT rows ready for loading
    """
    routers: list[dict] = []
    cloud_nats: list[dict] = []

    for scope, scoped_list in response.get("items", {}).items():
        region = _scope_to_region(scope)
        for router in scoped_list.get("routers", []):
            router_partial_uri = (
                f"projects/{project_id}/{scope}/routers/{router['name']}"
            )
            network = router.get("network")
            router_row: dict[str, Any] = {
                "partial_uri": router_partial_uri,
                "project_id": project_id,
                "region": region,
                "name": router.get("name"),
                "self_link": router.get("selfLink"),
                "description": router.get("description"),
                "network_partial_uri": parse_compute_full_uri_to_partial_uri(network),
            }
            routers.append(router_row)

            for nat in router.get("nats", []) or []:
                nat_name = nat.get("name")
                if not nat_name:
                    continue
                log_config = nat.get("logConfig", {})
                cloud_nats.append(
                    {
                        "id": f"{router_partial_uri}/nats/{nat_name}",
                        "name": nat_name,
                        "project_id": project_id,
                        "region": region,
                        "router_id": router_partial_uri,
                        "log_enabled": log_config.get("enable"),
                        "log_filter": log_config.get("filter"),
                        "nat_ip_allocate_option": nat.get("natIpAllocateOption"),
                        "source_subnetwork_ip_ranges_to_nat": nat.get(
                            "sourceSubnetworkIpRangesToNat"
                        ),
                    },
                )
    return routers, cloud_nats


@timeit
def load_gcp_routers(
    neo4j_session: neo4j.Session,
    routers: list[dict],
    gcp_update_tag: int,
    project_id: str,
) -> None:
    load(
        neo4j_session,
        GCPRouterSchema(),
        routers,
        lastupdated=gcp_update_tag,
        PROJECT_ID=project_id,
    )


@timeit
def load_gcp_cloud_nats(
    neo4j_session: neo4j.Session,
    cloud_nats: list[dict],
    gcp_update_tag: int,
    project_id: str,
) -> None:
    load(
        neo4j_session,
        GCPCloudNatSchema(),
        cloud_nats,
        lastupdated=gcp_update_tag,
        PROJECT_ID=project_id,
    )


@timeit
def cleanup_gcp_routers(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict,
) -> None:
    GraphJob.from_node_schema(GCPCloudNatSchema(), common_job_parameters).run(
        neo4j_session,
    )
    GraphJob.from_node_schema(GCPRouterSchema(), common_job_parameters).run(
        neo4j_session,
    )


@timeit
def sync_gcp_routers(
    neo4j_session: neo4j.Session,
    compute: Resource,
    project_id: str,
    gcp_update_tag: int,
    common_job_parameters: dict,
) -> None:
    """
    Sync GCP Cloud Routers and nested Cloud NAT configs.
    """
    logger.info(
        "Syncing GCP Cloud Routers and Cloud NAT configs for project %s", project_id
    )
    response = get_gcp_routers(project_id, compute)
    if response is None:
        return
    routers, cloud_nats = transform_gcp_routers(response, project_id)
    load_gcp_routers(neo4j_session, routers, gcp_update_tag, project_id)
    load_gcp_cloud_nats(neo4j_session, cloud_nats, gcp_update_tag, project_id)

    if aggregated_response_cleanup_safe(response):
        cleanup_gcp_routers(neo4j_session, common_job_parameters)
