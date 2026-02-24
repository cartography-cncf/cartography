# Google Compute Engine Instance Groups
# https://cloud.google.com/compute/docs/reference/rest/v1/instanceGroups
# https://cloud.google.com/compute/docs/reference/rest/v1/regionInstanceGroups
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
from cartography.models.gcp.compute.instance_group import GCPInstanceGroupSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


def _get_instance_group_members(
    project_id: str,
    instance_group_name: str,
    zone: str | None,
    region: str | None,
    compute: Resource,
) -> list[dict]:
    """
    Return list of member instances for a given instance group.
    :param project_id: The project ID
    :param instance_group_name: The name of the instance group
    :param zone: The zone (for zonal instance groups), or None
    :param region: The region (for regional instance groups), or None
    :param compute: The compute resource object
    :return: List of member dicts with 'instance' (URL) and 'status' fields
    """
    if zone:
        req = compute.instanceGroups().listInstances(
            project=project_id,
            zone=zone,
            instanceGroup=instance_group_name,
            body={"instanceState": "ALL"},
        )
        list_next_fn = compute.instanceGroups().listInstances_next
    elif region:
        req = compute.regionInstanceGroups().listInstances(
            project=project_id,
            region=region,
            instanceGroup=instance_group_name,
            body={"instanceState": "ALL"},
        )
        list_next_fn = compute.regionInstanceGroups().listInstances_next
    else:
        return []

    members: list[dict] = []
    while req is not None:
        try:
            res = gcp_api_execute_with_retry(req)
        except HttpError as e:
            reason = get_error_reason(e)
            if reason in {"backendError", "rateLimitExceeded", "internalError"}:
                logger.warning(
                    "Transient error listing members for instance group %s: %s; skipping.",
                    instance_group_name,
                    e,
                )
                return []
            raise
        members.extend(res.get("items", []))
        req = list_next_fn(previous_request=req, previous_response=res)
    return members


@timeit
def get_gcp_zonal_instance_groups(
    project_id: str,
    zones: list[dict],
    compute: Resource,
) -> list[Resource]:
    """
    Return list of instance group response objects across all zones in a project.
    Each instance group item is enriched with a '_members' field containing its member instances.
    :param project_id: The project ID
    :param zones: The list of zones to query
    :param compute: The compute resource object
    :return: A list of response objects of the form {id: str, items: [...]}
    """
    response_objects: list[Resource] = []
    for zone in zones:
        items: list[dict] = []
        response_id = f"projects/{project_id}/zones/{zone['name']}/instanceGroups"
        req = compute.instanceGroups().list(project=project_id, zone=zone["name"])
        while req is not None:
            try:
                res = gcp_api_execute_with_retry(req)
            except HttpError as e:
                reason = get_error_reason(e)
                if reason in {"backendError", "rateLimitExceeded", "internalError"}:
                    logger.warning(
                        "Transient error listing instance groups for project %s zone %s: %s; skipping.",
                        project_id,
                        zone.get("name"),
                        e,
                    )
                    break
                raise
            items.extend(res.get("items", []))
            response_id = res.get("id", response_id)
            req = compute.instanceGroups().list_next(
                previous_request=req, previous_response=res
            )

        if not items:
            continue

        for ig in items:
            ig["_members"] = _get_instance_group_members(
                project_id,
                ig["name"],
                zone["name"],
                None,
                compute,
            )
        if items:
            response_objects.append({"id": response_id, "items": items})
    return response_objects


@timeit
def get_gcp_regional_instance_groups(
    project_id: str,
    regions: list[str],
    compute: Resource,
) -> list[Resource]:
    """
    Return list of instance group response objects across all regions in a project.
    Each instance group item is enriched with a '_members' field containing its member instances.
    :param project_id: The project ID
    :param regions: The list of region names to query
    :param compute: The compute resource object
    :return: A list of response objects of the form {id: str, items: [...]}
    """
    response_objects: list[Resource] = []
    for region in regions:
        items: list[dict] = []
        response_id = f"projects/{project_id}/regions/{region}/instanceGroups"
        req = compute.regionInstanceGroups().list(project=project_id, region=region)
        # Track invalid regions so we can skip them entirely rather than ingesting partial data
        skip_region = False
        while req is not None:
            try:
                res = gcp_api_execute_with_retry(req)
            except HttpError as e:
                reason = get_error_reason(e)
                if reason == "invalid":
                    logger.warning(
                        "GCP: Invalid region %s for project %s; skipping instance groups sync for this region.",
                        region,
                        project_id,
                    )
                    skip_region = True
                    break
                raise
            items.extend(res.get("items", []))
            response_id = res.get("id", response_id)
            req = compute.regionInstanceGroups().list_next(
                previous_request=req, previous_response=res
            )

        if skip_region:
            continue

        for ig in items:
            ig["_members"] = _get_instance_group_members(
                project_id,
                ig["name"],
                None,
                region,
                compute,
            )
        if items:
            response_objects.append({"id": response_id, "items": items})
    return response_objects


@timeit
def transform_gcp_instance_groups(
    response_objects: list[Resource],
    project_id: str,
) -> list[dict]:
    """
    Transform instance group response objects for Neo4j ingestion.
    Expects each instance group item to have a '_members' field populated by the get functions.
    :param response_objects: List of response objects from the get functions
    :param project_id: The project ID
    :return: List of transformed instance group dicts ready for loading
    """
    instance_group_list: list[dict] = []

    for response in response_objects:
        prefix = response["id"]

        for ig in response.get("items", []):
            instance_group: dict[str, Any] = {}

            partial_uri = f"{prefix}/{ig['name']}"
            instance_group["partial_uri"] = partial_uri
            instance_group["project_id"] = project_id
            instance_group["name"] = ig.get("name")
            instance_group["self_link"] = ig.get("selfLink")
            instance_group["description"] = ig.get("description")
            instance_group["size"] = ig.get("size")
            instance_group["creation_timestamp"] = ig.get("creationTimestamp")

            zone_url = ig.get("zone")
            instance_group["zone"] = zone_url.split("/")[-1] if zone_url else None

            region_url = ig.get("region")
            instance_group["region"] = region_url.split("/")[-1] if region_url else None

            network = ig.get("network")
            instance_group["network_partial_uri"] = (
                parse_compute_full_uri_to_partial_uri(network)
            )

            subnetwork = ig.get("subnetwork")
            instance_group["subnetwork_partial_uri"] = (
                parse_compute_full_uri_to_partial_uri(subnetwork)
            )

            # Member instances from _members (populated by get functions)
            instance_group["member_instance_partial_uris"] = [
                parse_compute_full_uri_to_partial_uri(member_url)
                for m in ig.get("_members", [])
                if (member_url := m.get("instance"))
            ]

            instance_group_list.append(instance_group)
    return instance_group_list


@timeit
def load_gcp_instance_groups(
    neo4j_session: neo4j.Session,
    instance_groups: list[dict],
    gcp_update_tag: int,
    project_id: str,
) -> None:
    """
    Ingest GCP instance group data to Neo4j.
    """
    load(
        neo4j_session,
        GCPInstanceGroupSchema(),
        instance_groups,
        lastupdated=gcp_update_tag,
        PROJECT_ID=project_id,
    )


@timeit
def cleanup_gcp_instance_groups(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict,
) -> None:
    """
    Delete out-of-date GCP instance groups and relationships.
    """
    GraphJob.from_node_schema(GCPInstanceGroupSchema(), common_job_parameters).run(
        neo4j_session,
    )


@timeit
def sync_gcp_instance_groups(
    neo4j_session: neo4j.Session,
    compute: Resource,
    project_id: str,
    zones: list[dict],
    regions: list[str],
    gcp_update_tag: int,
    common_job_parameters: dict,
) -> None:
    """
    Sync GCP zonal and regional instance groups, ingest to Neo4j, and clean up old data.
    """
    logger.info("Syncing GCP instance groups for project %s", project_id)

    # Zonal instance groups
    zonal_responses = get_gcp_zonal_instance_groups(project_id, zones, compute)
    instance_groups = transform_gcp_instance_groups(zonal_responses, project_id)
    load_gcp_instance_groups(neo4j_session, instance_groups, gcp_update_tag, project_id)

    # Regional instance groups
    regional_responses = get_gcp_regional_instance_groups(project_id, regions, compute)
    instance_groups = transform_gcp_instance_groups(regional_responses, project_id)
    load_gcp_instance_groups(neo4j_session, instance_groups, gcp_update_tag, project_id)

    # Cleanup after both zonal and regional are loaded
    cleanup_gcp_instance_groups(neo4j_session, common_job_parameters)
