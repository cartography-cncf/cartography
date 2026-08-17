# Google Compute Engine SSL Policies
# https://cloud.google.com/compute/docs/reference/rest/v1/sslPolicies
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
from cartography.intel.gcp.util import summarize_gcp_http_error
from cartography.models.gcp.compute.ssl_policy import GCPSslPolicySchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_gcp_ssl_policies(
    project_id: str,
    compute: Resource,
) -> Resource | None:
    """
    Return all global and regional SSL policies in the given project.
    :param project_id: The project ID
    :param compute: The compute resource object created by googleapiclient.discovery.build()
    :return: Aggregated response object containing SSL policies, or None if access is denied
    """
    items: dict[str, dict] = {}
    response_id = f"projects/{project_id}/aggregated/sslPolicies"
    req = compute.sslPolicies().aggregatedList(
        project=project_id,
        returnPartialSuccess=True,
    )
    while req is not None:
        try:
            res = gcp_api_execute_with_retry(req)
        except HttpError as e:
            if classify_gcp_http_error(e) in GCP_EXPECTED_SKIP_CATEGORIES:
                logger.warning(
                    "GCP: Unable to list SSL policies for project %s; skipping this collector. %s",
                    project_id,
                    summarize_gcp_http_error(e),
                )
                return None
            raise
        merge_aggregated_scope_items(items, res, "sslPolicies")
        response_id = res.get("id", response_id)
        req = compute.sslPolicies().aggregatedList_next(
            previous_request=req,
            previous_response=res,
        )
    return {"id": response_id, "items": items}


def _transform_gcp_ssl_policy(
    policy: dict[str, Any],
    project_id: str,
    scope: str,
) -> dict[str, Any]:
    partial_uri = f"projects/{project_id}/{scope}/sslPolicies/{policy['name']}"
    transformed: dict[str, Any] = {}
    transformed["partial_uri"] = partial_uri
    transformed["project_id"] = project_id
    transformed["region"] = None if scope == "global" else scope.split("regions/")[-1]
    transformed["name"] = policy.get("name")
    transformed["self_link"] = policy.get("selfLink")
    transformed["description"] = policy.get("description")
    transformed["profile"] = policy.get("profile")
    transformed["min_tls_version"] = policy.get("minTlsVersion")
    transformed["enabled_features"] = policy.get("enabledFeatures", [])
    transformed["custom_features"] = policy.get("customFeatures", [])
    transformed["creation_timestamp"] = policy.get("creationTimestamp")
    return transformed


@timeit
def transform_gcp_ssl_policies(response: Resource, project_id: str) -> list[dict]:
    """
    Transform the SSL policy response object for Neo4j ingestion.
    :param response: The response object returned from sslPolicies.aggregatedList()
    :param project_id: The GCP project ID
    :return: List of transformed policy dicts ready for loading
    """
    policy_list: list[dict] = []

    for scope, scoped_list in response.get("items", {}).items():
        for policy in scoped_list.get("sslPolicies", []):
            policy_list.append(_transform_gcp_ssl_policy(policy, project_id, scope))
    return policy_list


@timeit
def load_gcp_ssl_policies(
    neo4j_session: neo4j.Session,
    policies: list[dict],
    gcp_update_tag: int,
    project_id: str,
) -> None:
    """
    Ingest GCP SSL policy data to Neo4j.
    """
    load(
        neo4j_session,
        GCPSslPolicySchema(),
        policies,
        lastupdated=gcp_update_tag,
        PROJECT_ID=project_id,
    )


@timeit
def cleanup_gcp_ssl_policies(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict,
) -> None:
    """
    Delete out-of-date GCP SSL policies and relationships.
    """
    GraphJob.from_node_schema(GCPSslPolicySchema(), common_job_parameters).run(
        neo4j_session,
    )


@timeit
def sync_gcp_ssl_policies(
    neo4j_session: neo4j.Session,
    compute: Resource,
    project_id: str,
    gcp_update_tag: int,
    common_job_parameters: dict,
) -> None:
    """
    Sync GCP global and regional SSL policies, ingest to Neo4j, and clean up old data.
    """
    logger.info("Syncing GCP SSL policies for project %s", project_id)
    response = get_gcp_ssl_policies(project_id, compute)
    if response is None:
        return
    policies = transform_gcp_ssl_policies(response, project_id)
    load_gcp_ssl_policies(neo4j_session, policies, gcp_update_tag, project_id)

    if aggregated_response_cleanup_safe(response):
        cleanup_gcp_ssl_policies(neo4j_session, common_job_parameters)
