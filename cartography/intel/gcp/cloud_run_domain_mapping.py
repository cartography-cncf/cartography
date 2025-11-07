import logging

import neo4j
from googleapiclient.discovery import Resource

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.gcp.cloudrun.domain_mapping import (
    GCPCloudRunDomainMappingSchema,
)
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_cloud_run_domain_mappings(client: Resource, location_name: str) -> list[dict]:
    mappings: list[dict] = []
    request = client.projects().locations().domainmappings().list(parent=location_name)
    response = request.execute()
    mappings.extend(response.get("domainMappings", []))
    return mappings


def transform_domain_mappings(mappings_data: list[dict], project_id: str) -> list[dict]:
    transformed: list[dict] = []
    for mapping in mappings_data:
        mapping_id = mapping.get("name")
        if not mapping_id:
            continue
        transformed.append(
            {
                "id": mapping_id,
                "name": mapping_id.split("/")[-1],
                "route_name": mapping.get("spec", {}).get("routeName"),
                "project_id": project_id,
            },
        )
    return transformed


@timeit
def load_cloud_run_domain_mappings(
    neo4j_session: neo4j.Session,
    data: list[dict],
    project_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        GCPCloudRunDomainMappingSchema(),
        data,
        lastupdated=update_tag,
        project_id=project_id,
    )


@timeit
def cleanup_cloud_run_domain_mappings(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict,
) -> None:
    GraphJob.from_node_schema(
        GCPCloudRunDomainMappingSchema(),
        common_job_parameters,
    ).run(neo4j_session)


@timeit
def sync_cloud_run_domain_mappings(
    neo4j_session: neo4j.Session,
    client: Resource,
    locations: list[dict],
    project_id: str,
    update_tag: int,
    common_job_parameters: dict,
) -> None:
    logger.info(f"Syncing Cloud Run Domain Mappings for project {project_id}.")
    all_domain_mappings_raw: list[dict] = []
    for loc in locations:
        location_id = loc.get("locationId")
        if not location_id:
            continue
        location_name = f"projects/{project_id}/locations/{location_id}"
        all_domain_mappings_raw.extend(
            get_cloud_run_domain_mappings(client, location_name),
        )

    domain_mappings = transform_domain_mappings(all_domain_mappings_raw, project_id)
    load_cloud_run_domain_mappings(
        neo4j_session,
        domain_mappings,
        project_id,
        update_tag,
    )

    cleanup_job_params = common_job_parameters.copy()
    cleanup_job_params["project_id"] = project_id
    cleanup_cloud_run_domain_mappings(neo4j_session, cleanup_job_params)
