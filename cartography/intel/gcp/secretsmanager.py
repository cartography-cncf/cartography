import json
import logging
from datetime import datetime
from typing import Dict
from typing import List

import neo4j
from googleapiclient.discovery import HttpError
from googleapiclient.discovery import Resource

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.gcp import compute
from cartography.intel.gcp.util import gcp_api_execute_with_retry
from cartography.models.gcp.secretsmanager.secret import GCPSecretManagerSecretSchema
from cartography.models.gcp.secretsmanager.secret_version import (
    GCPSecretManagerSecretVersionSchema,
)
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_secrets(secretmanager: Resource, project_id: str) -> List[Dict]:
    """
    Get all secrets from GCP Secret Manager for a given project.
    """
    try:
        secrets: List[Dict] = []
        parent = f"projects/{project_id}"
        req = secretmanager.projects().secrets().list(parent=parent)
        while req is not None:
            res = gcp_api_execute_with_retry(req)
            secrets.extend(res.get("secrets", []))
            req = (
                secretmanager.projects()
                .secrets()
                .list_next(
                    previous_request=req,
                    previous_response=res,
                )
            )
        return secrets
    except HttpError as e:
        reason = compute._get_error_reason(e)
        if reason == "invalid":
            logger.warning(
                (
                    "The project %s is invalid - returned a 400 invalid error. "
                    "Full details: %s"
                ),
                project_id,
                e,
            )
            return []
        elif reason == "forbidden":
            logger.warning(
                (
                    "You do not have secretmanager.secrets.list access to the project %s. "
                    "Full details: %s"
                ),
                project_id,
                e,
            )
            return []
        else:
            raise


@timeit
def get_secret_versions(
    secretmanager: Resource,
    secret_name: str,
) -> List[Dict]:
    """
    Get all versions of a secret from GCP Secret Manager.
    """
    try:
        versions: List[Dict] = []
        req = secretmanager.projects().secrets().versions().list(parent=secret_name)
        while req is not None:
            res = gcp_api_execute_with_retry(req)
            versions.extend(res.get("versions", []))
            req = (
                secretmanager.projects()
                .secrets()
                .versions()
                .list_next(
                    previous_request=req,
                    previous_response=res,
                )
            )
        return versions
    except HttpError as e:
        reason = compute._get_error_reason(e)
        if reason == "invalid":
            logger.warning(
                (
                    "The secret %s is invalid - returned a 400 invalid error. "
                    "Full details: %s"
                ),
                secret_name,
                e,
            )
            return []
        elif reason == "forbidden":
            logger.warning(
                (
                    "You do not have secretmanager.versions.list access to the secret %s. "
                    "Full details: %s"
                ),
                secret_name,
                e,
            )
            return []
        else:
            raise


def transform_secrets(secrets: List[Dict]) -> List[Dict]:
    """
    Transform GCP Secret Manager secrets to match the data model.
    """
    transformed = []
    for secret in secrets:
        # Parse name: "projects/{project_id}/secrets/{secret_name}"
        name_parts = secret["name"].split("/")
        project_id = name_parts[1]
        secret_name = name_parts[3]

        # Parse timestamps
        create_time = secret.get("createTime")
        created_date = None
        if create_time:
            dt = datetime.fromisoformat(create_time.replace("Z", "+00:00"))
            created_date = int(dt.timestamp())

        expire_time_str = secret.get("expireTime")
        expire_time = None
        if expire_time_str:
            dt = datetime.fromisoformat(expire_time_str.replace("Z", "+00:00"))
            expire_time = int(dt.timestamp())

        # Parse rotation
        rotation = secret.get("rotation", {})
        rotation_enabled = bool(rotation)
        rotation_period = None
        rotation_next_time = None
        if rotation:
            period_str = rotation.get("rotationPeriod")
            if period_str:
                rotation_period = int(period_str.rstrip("s"))
            next_time_str = rotation.get("nextRotationTime")
            if next_time_str:
                dt = datetime.fromisoformat(next_time_str.replace("Z", "+00:00"))
                rotation_next_time = int(dt.timestamp())

        # Parse replication type
        replication = secret.get("replication", {})
        replication_type = "automatic" if "automatic" in replication else "user_managed"

        # Convert complex types to JSON strings for Neo4j storage
        labels = secret.get("labels")
        topics = secret.get("topics")
        version_aliases = secret.get("versionAliases")

        transformed.append(
            {
                "id": secret["name"],
                "name": secret_name,
                "project_id": project_id,
                "rotation_enabled": rotation_enabled,
                "rotation_period": rotation_period,
                "rotation_next_time": rotation_next_time,
                "created_date": created_date,
                "expire_time": expire_time,
                "replication_type": replication_type,
                "etag": secret.get("etag"),
                "labels": json.dumps(labels) if labels else None,
                "topics": json.dumps(topics) if topics else None,
                "version_aliases": (
                    json.dumps(version_aliases) if version_aliases else None
                ),
            }
        )

    return transformed


def transform_secret_versions(versions: List[Dict]) -> List[Dict]:
    """
    Transform GCP Secret Manager secret versions to match the data model.
    """
    transformed = []
    for version in versions:
        # Parse name: "projects/{project}/secrets/{secret}/versions/{version}"
        name_parts = version["name"].split("/")
        secret_id = "/".join(name_parts[:4])  # projects/{project}/secrets/{secret}
        version_num = name_parts[5]

        # Parse timestamps
        create_time = version.get("createTime")
        created_date = None
        if create_time:
            dt = datetime.fromisoformat(create_time.replace("Z", "+00:00"))
            created_date = int(dt.timestamp())

        destroy_time_str = version.get("destroyTime")
        destroy_time = None
        if destroy_time_str:
            dt = datetime.fromisoformat(destroy_time_str.replace("Z", "+00:00"))
            destroy_time = int(dt.timestamp())

        transformed.append(
            {
                "id": version["name"],
                "secret_id": secret_id,
                "version": version_num,
                "state": version.get("state"),
                "created_date": created_date,
                "destroy_time": destroy_time,
                "etag": version.get("etag"),
            }
        )

    return transformed


@timeit
def load_secrets(
    neo4j_session: neo4j.Session,
    secrets: List[Dict],
    project_id: str,
    gcp_update_tag: int,
) -> None:
    """
    Load transformed secrets into Neo4j.
    """
    logger.info(f"Loading {len(secrets)} secrets for project {project_id} into graph.")
    load(
        neo4j_session,
        GCPSecretManagerSecretSchema(),
        secrets,
        lastupdated=gcp_update_tag,
        PROJECT_ID=project_id,
    )


@timeit
def cleanup_secrets(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict,
) -> None:
    """
    Run cleanup job for secrets.
    """
    logger.debug("Running GCP Secret Manager secrets cleanup job.")
    GraphJob.from_node_schema(
        GCPSecretManagerSecretSchema(),
        common_job_parameters,
    ).run(neo4j_session)


@timeit
def load_secret_versions(
    neo4j_session: neo4j.Session,
    versions: List[Dict],
    project_id: str,
    gcp_update_tag: int,
) -> None:
    """
    Load transformed secret versions into Neo4j.
    """
    logger.info(
        f"Loading {len(versions)} secret versions for project {project_id} into graph."
    )
    load(
        neo4j_session,
        GCPSecretManagerSecretVersionSchema(),
        versions,
        lastupdated=gcp_update_tag,
        PROJECT_ID=project_id,
    )


@timeit
def cleanup_secret_versions(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict,
) -> None:
    """
    Run cleanup job for secret versions.
    """
    logger.debug("Running GCP Secret Manager secret versions cleanup job.")
    GraphJob.from_node_schema(
        GCPSecretManagerSecretVersionSchema(),
        common_job_parameters,
    ).run(neo4j_session)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    secretmanager: Resource,
    project_id: str,
    gcp_update_tag: int,
    common_job_parameters: Dict,
) -> None:
    """
    Sync GCP Secret Manager secrets and secret versions for a project.
    """
    logger.info(f"Syncing Secret Manager for project {project_id}.")

    # Sync secrets
    secrets = get_secrets(secretmanager, project_id)
    transformed_secrets = transform_secrets(secrets)
    load_secrets(neo4j_session, transformed_secrets, project_id, gcp_update_tag)

    # Sync secret versions
    all_versions: List[Dict] = []
    for secret in secrets:
        versions = get_secret_versions(secretmanager, secret["name"])
        all_versions.extend(versions)

    transformed_versions = transform_secret_versions(all_versions)
    load_secret_versions(
        neo4j_session, transformed_versions, project_id, gcp_update_tag
    )

    # Cleanup
    cleanup_secret_versions(neo4j_session, common_job_parameters)
    cleanup_secrets(neo4j_session, common_job_parameters)
