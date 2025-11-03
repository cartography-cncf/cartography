import logging
from typing import Any
from typing import Dict
from typing import List

import neo4j
from google.api_core.exceptions import PermissionDenied
from google.auth.exceptions import DefaultCredentialsError
from google.auth.exceptions import RefreshError
from googleapiclient.discovery import HttpError
from googleapiclient.discovery import Resource

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.gcp.bigtable.app_profile import GCPBigtableAppProfileSchema
from cartography.models.gcp.bigtable.backup import GCPBigtableBackupSchema
from cartography.models.gcp.bigtable.cluster import GCPBigtableClusterSchema
from cartography.models.gcp.bigtable.instance import GCPBigtableInstanceSchema
from cartography.models.gcp.bigtable.table import GCPBigtableTableSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_bigtable_instances(client: Resource, project_id: str) -> List[Dict]:
    instances: List[Dict] = []
    try:
        request = client.projects().instances().list(parent=f"projects/{project_id}")
        while request is not None:
            response = request.execute()
            instances.extend(response.get("instances", []))
            request = (
                client.projects()
                .instances()
                .list_next(
                    previous_request=request,
                    previous_response=response,
                )
            )
        return instances
    except (PermissionDenied, DefaultCredentialsError, RefreshError) as e:
        logger.warning(
            f"Failed to get Bigtable instances for project {project_id} due to permissions or auth error: {e}",
        )
        raise
    except HttpError:
        logger.warning(
            f"Failed to get Bigtable instances for project {project_id} due to a transient HTTP error.",
            exc_info=True,
        )
        return []


@timeit
def get_bigtable_clusters(client: Resource, instance_id: str) -> List[Dict]:
    clusters: List[Dict] = []
    try:
        request = client.projects().instances().clusters().list(parent=instance_id)
        while request is not None:
            response = request.execute()
            clusters.extend(response.get("clusters", []))
            request = (
                client.projects()
                .instances()
                .clusters()
                .list_next(
                    previous_request=request,
                    previous_response=response,
                )
            )
        return clusters
    except HttpError:
        logger.warning(
            f"Failed to get Bigtable clusters for instance {instance_id} due to a transient HTTP error.",
            exc_info=True,
        )
        return []


@timeit
def get_bigtable_tables(client: Resource, instance_id: str) -> List[Dict]:
    tables: List[Dict] = []
    try:
        request = client.projects().instances().tables().list(parent=instance_id)
        while request is not None:
            response = request.execute()
            tables.extend(response.get("tables", []))
            request = (
                client.projects()
                .instances()
                .tables()
                .list_next(
                    previous_request=request,
                    previous_response=response,
                )
            )
        return tables
    except HttpError:
        logger.warning(
            f"Failed to get Bigtable tables for instance {instance_id} due to a transient HTTP error.",
            exc_info=True,
        )
        return []


@timeit
def get_bigtable_app_profiles(client: Resource, instance_id: str) -> List[Dict]:
    app_profiles: List[Dict] = []
    try:
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
    except HttpError:
        logger.warning(
            f"Failed to get Bigtable app profiles for instance {instance_id} due to a transient HTTP error.",
            exc_info=True,
        )
        return []


@timeit
def get_bigtable_backups(client: Resource, cluster_id: str) -> List[Dict]:
    backups: List[Dict] = []
    try:
        request = (
            client.projects().instances().clusters().backups().list(parent=cluster_id)
        )
        while request is not None:
            response = request.execute()
            backups.extend(response.get("backups", []))
            request = (
                client.projects()
                .instances()
                .clusters()
                .backups()
                .list_next(
                    previous_request=request,
                    previous_response=response,
                )
            )
        return backups
    except HttpError:
        logger.warning(
            f"Failed to get Bigtable backups for cluster {cluster_id} due to a transient HTTP error.",
            exc_info=True,
        )
        return []


def transform_instances(instances_data: List[Dict], project_id: str) -> List[Dict]:
    transformed: List[Dict] = []
    for inst in instances_data:
        inst["project_id"] = project_id
        transformed.append(inst)
    return transformed


def transform_clusters(clusters_data: List[Dict], instance_id: str) -> List[Dict]:
    transformed: List[Dict] = []
    for cluster in clusters_data:
        cluster["instance_id"] = instance_id
        transformed.append(cluster)
    return transformed


def transform_tables(tables_data: List[Dict], instance_id: str) -> List[Dict]:
    transformed: List[Dict] = []
    for table in tables_data:
        table["instance_id"] = instance_id
        transformed.append(table)
    return transformed


def transform_app_profiles(
    app_profiles_data: List[Dict], instance_id: str
) -> List[Dict]:
    """
    Transforms the list of App Profile dicts for ingestion.
    """
    transformed: List[Dict] = []
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


def transform_backups(backups_data: List[Dict], cluster_id: str) -> List[Dict]:
    transformed: List[Dict] = []
    for backup in backups_data:
        backup["cluster_id"] = cluster_id
        backup["source_table"] = backup.get("sourceTable")
        transformed.append(backup)
    return transformed


@timeit
def load_bigtable_instances(
    neo4j_session: neo4j.Session, data: List[Dict], project_id: str, update_tag: int
) -> None:
    load(
        neo4j_session,
        GCPBigtableInstanceSchema(),
        data,
        lastupdated=update_tag,
        PROJECT_ID=project_id,
    )


@timeit
def load_bigtable_clusters(
    neo4j_session: neo4j.Session, data: List[Dict], project_id: str, update_tag: int
) -> None:
    load(
        neo4j_session,
        GCPBigtableClusterSchema(),
        data,
        lastupdated=update_tag,
        PROJECT_ID=project_id,
    )


@timeit
def load_bigtable_tables(
    neo4j_session: neo4j.Session, data: List[Dict], project_id: str, update_tag: int
) -> None:
    load(
        neo4j_session,
        GCPBigtableTableSchema(),
        data,
        lastupdated=update_tag,
        PROJECT_ID=project_id,
    )


@timeit
def load_bigtable_app_profiles(
    neo4j_session: neo4j.Session, data: List[Dict], project_id: str, update_tag: int
) -> None:
    load(
        neo4j_session,
        GCPBigtableAppProfileSchema(),
        data,
        lastupdated=update_tag,
        PROJECT_ID=project_id,
    )


@timeit
def load_bigtable_backups(
    neo4j_session: neo4j.Session, data: List[Dict], project_id: str, update_tag: int
) -> None:
    load(
        neo4j_session,
        GCPBigtableBackupSchema(),
        data,
        lastupdated=update_tag,
        PROJECT_ID=project_id,
    )


@timeit
def cleanup_bigtable(neo4j_session: neo4j.Session, common_job_parameters: dict) -> None:
    GraphJob.from_node_schema(GCPBigtableBackupSchema(), common_job_parameters).run(
        neo4j_session
    )
    GraphJob.from_node_schema(GCPBigtableAppProfileSchema(), common_job_parameters).run(
        neo4j_session
    )
    GraphJob.from_node_schema(GCPBigtableTableSchema(), common_job_parameters).run(
        neo4j_session
    )
    GraphJob.from_node_schema(GCPBigtableClusterSchema(), common_job_parameters).run(
        neo4j_session
    )
    GraphJob.from_node_schema(GCPBigtableInstanceSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    bigtable_client: Resource,
    project_id: str,
    gcp_update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    logger.info(f"Syncing GCP Bigtable for project {project_id}.")

    instances_raw = get_bigtable_instances(bigtable_client, project_id)
    if not instances_raw:
        logger.info(f"No Bigtable instances found for project {project_id}.")
    else:
        instances = transform_instances(instances_raw, project_id)
        load_bigtable_instances(neo4j_session, instances, project_id, gcp_update_tag)

        all_clusters: List[Dict] = []
        all_tables: List[Dict] = []
        all_app_profiles: List[Dict] = []
        all_backups: List[Dict] = []

        for inst in instances_raw:
            instance_id = inst["name"]

            clusters_raw = get_bigtable_clusters(bigtable_client, instance_id)
            all_clusters.extend(transform_clusters(clusters_raw, instance_id))

            tables_raw = get_bigtable_tables(bigtable_client, instance_id)
            all_tables.extend(transform_tables(tables_raw, instance_id))

            app_profiles_raw = get_bigtable_app_profiles(bigtable_client, instance_id)
            all_app_profiles.extend(
                transform_app_profiles(app_profiles_raw, instance_id)
            )

            for cluster in clusters_raw:
                cluster_id = cluster["name"]
                backups_raw = get_bigtable_backups(bigtable_client, cluster_id)
                all_backups.extend(transform_backups(backups_raw, cluster_id))

        load_bigtable_clusters(neo4j_session, all_clusters, project_id, gcp_update_tag)
        load_bigtable_tables(neo4j_session, all_tables, project_id, gcp_update_tag)
        load_bigtable_app_profiles(
            neo4j_session, all_app_profiles, project_id, gcp_update_tag
        )
        load_bigtable_backups(neo4j_session, all_backups, project_id, gcp_update_tag)

    cleanup_job_params = common_job_parameters.copy()
    cleanup_job_params["PROJECT_ID"] = project_id
    cleanup_bigtable(neo4j_session, cleanup_job_params)
