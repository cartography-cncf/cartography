import logging

import neo4j
from googleapiclient.discovery import Resource

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.gcp.bigtable.app_profile import GCPBigtableAppProfileSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_bigtable_app_profiles(client: Resource, instance_id: str) -> list[dict]:
    app_profiles: list[dict] = []
    request = client.projects().instances().appProfiles().list(parent=instance_id)
    while request is not None:
        response = request.execute()
        app_profiles.extend(response.get("appProfiles", []))
        request = (
            client.projects()
            .instances()
            .appProfiles()
            .list_next(
                previous_request=request,
                previous_response=response,
            )
        )
    return app_profiles


def transform_app_profiles(
    app_profiles_data: list[dict],
    instance_id: str,
) -> list[dict]:
    transformed: list[dict] = []
    for app_profile in app_profiles_data:
        app_profile["instance_id"] = instance_id
        routing = app_profile.get("singleClusterRouting")
        if routing:
            short_cluster_id = routing.get("clusterId")
            if short_cluster_id:
                app_profile["single_cluster_routing_cluster_id"] = (
                    f"{instance_id}/clusters/{short_cluster_id}"
                )
        transformed.append(app_profile)
    return transformed


@timeit
def load_bigtable_app_profiles(
    neo4j_session: neo4j.Session,
    data: list[dict],
    project_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        GCPBigtableAppProfileSchema(),
        data,
        lastupdated=update_tag,
        PROJECT_ID=project_id,
    )


@timeit
def cleanup_bigtable_app_profiles(
    neo4j_session: neo4j.Session, common_job_parameters: dict
) -> None:
    GraphJob.from_node_schema(GCPBigtableAppProfileSchema(), common_job_parameters).run(
        neo4j_session,
    )


@timeit
def sync_bigtable_app_profiles(
    neo4j_session: neo4j.Session,
    client: Resource,
    instances: list[dict],
    project_id: str,
    update_tag: int,
    common_job_parameters: dict,
) -> None:
    logger.info(f"Syncing Bigtable App Profiles for project {project_id}.")
    all_app_profiles_transformed: list[dict] = []

    for inst in instances:
        instance_id = inst["name"]
        app_profiles_raw = get_bigtable_app_profiles(client, instance_id)
        all_app_profiles_transformed.extend(
            transform_app_profiles(app_profiles_raw, instance_id),
        )

    load_bigtable_app_profiles(
        neo4j_session, all_app_profiles_transformed, project_id, update_tag
    )

    cleanup_job_params = common_job_parameters.copy()
    cleanup_job_params["PROJECT_ID"] = project_id
    cleanup_bigtable_app_profiles(neo4j_session, cleanup_job_params)
