# Google Cloud Armor Security Policies
# https://cloud.google.com/compute/docs/reference/rest/v1/securityPolicies
from __future__ import annotations

import logging
from typing import Any

import neo4j
from googleapiclient.discovery import Resource

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.gcp.util import gcp_api_execute_with_retry
from cartography.models.gcp.compute.cloud_armor_policy import GCPCloudArmorPolicySchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_gcp_cloud_armor_policies(
    project_id: str,
    compute: Resource,
) -> Resource:
    """
    Return list of all Cloud Armor security policies in the given project.
    :param project_id: The project ID
    :param compute: The compute resource object created by googleapiclient.discovery.build()
    :return: Response object containing data on all security policies for a given project
    """
    items: list[dict] = []
    response_id = f"projects/{project_id}/global/securityPolicies"
    req = compute.securityPolicies().list(project=project_id)
    while req is not None:
        res = gcp_api_execute_with_retry(req)
        items.extend(res.get("items", []))
        response_id = res.get("id", response_id)
        req = compute.securityPolicies().list_next(
            previous_request=req, previous_response=res
        )
    return {"id": response_id, "items": items}


@timeit
def transform_gcp_cloud_armor_policies(
    response: Resource, project_id: str
) -> list[dict]:
    """
    Transform the security policy response object for Neo4j ingestion.
    :param response: The response object returned from securityPolicies.list()
    :param project_id: The GCP project ID
    :return: List of transformed policy dicts ready for loading
    """
    policy_list: list[dict] = []
    prefix = response["id"]

    for policy in response.get("items", []):
        transformed: dict[str, Any] = {}

        partial_uri = f"{prefix}/{policy['name']}"
        transformed["partial_uri"] = partial_uri
        transformed["project_id"] = project_id
        transformed["name"] = policy.get("name")
        transformed["self_link"] = policy.get("selfLink")
        transformed["description"] = policy.get("description")
        transformed["policy_type"] = policy.get("type")
        transformed["creation_timestamp"] = policy.get("creationTimestamp")

        policy_list.append(transformed)
    return policy_list


@timeit
def load_gcp_cloud_armor_policies(
    neo4j_session: neo4j.Session,
    policies: list[dict],
    gcp_update_tag: int,
    project_id: str,
) -> None:
    """
    Ingest GCP Cloud Armor security policy data to Neo4j.
    """
    load(
        neo4j_session,
        GCPCloudArmorPolicySchema(),
        policies,
        lastupdated=gcp_update_tag,
        PROJECT_ID=project_id,
    )


@timeit
def cleanup_gcp_cloud_armor_policies(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict,
) -> None:
    """
    Delete out-of-date GCP Cloud Armor security policies and relationships.
    """
    GraphJob.from_node_schema(GCPCloudArmorPolicySchema(), common_job_parameters).run(
        neo4j_session,
    )


@timeit
def sync_gcp_cloud_armor(
    neo4j_session: neo4j.Session,
    compute: Resource,
    project_id: str,
    gcp_update_tag: int,
    common_job_parameters: dict,
) -> None:
    """
    Sync GCP Cloud Armor security policies, ingest to Neo4j, and clean up old data.
    """
    logger.info("Syncing GCP Cloud Armor policies for project %s", project_id)
    response = get_gcp_cloud_armor_policies(project_id, compute)
    policies = transform_gcp_cloud_armor_policies(response, project_id)
    load_gcp_cloud_armor_policies(neo4j_session, policies, gcp_update_tag, project_id)
    cleanup_gcp_cloud_armor_policies(neo4j_session, common_job_parameters)
