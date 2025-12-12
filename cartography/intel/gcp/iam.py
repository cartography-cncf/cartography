import logging
from typing import Any
from typing import Dict
from typing import List

import neo4j
from googleapiclient.discovery import Resource

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.gcp.iam import GCPRoleSchema
from cartography.models.gcp.iam import GCPServiceAccountSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

# GCP API can be subject to rate limiting, so add small delays between calls
LIST_SLEEP = 1
DESCRIBE_SLEEP = 1


@timeit
def get_gcp_service_accounts(
    iam_client: Resource, project_id: str
) -> List[Dict[str, Any]]:
    """
    Retrieve a list of GCP service accounts for a given project.

    :param iam_client: The IAM resource object created by googleapiclient.discovery.build().
    :param project_id: The GCP Project ID to retrieve service accounts from.
    :return: A list of dictionaries representing GCP service accounts.
    """
    service_accounts: List[Dict[str, Any]] = []
    request = (
        iam_client.projects()
        .serviceAccounts()
        .list(
            name=f"projects/{project_id}",
        )
    )
    while request is not None:
        response = request.execute()
        if "accounts" in response:
            service_accounts.extend(response["accounts"])
        request = (
            iam_client.projects()
            .serviceAccounts()
            .list_next(
                previous_request=request,
                previous_response=response,
            )
        )
    return service_accounts


@timeit
def get_gcp_predefined_roles(iam_client: Resource) -> List[Dict]:
    """
    Retrieve all predefined (Google-managed) IAM roles.

    Predefined roles are global and not project-specific, so they can be fetched once
    and reused across all target projects. This is useful for the CAI fallback where
    the target project may not have the IAM API enabled.

    :param iam_client: The IAM resource object created by googleapiclient.discovery.build().
    :return: A list of dictionaries representing GCP predefined roles.
    """
    roles: List[Dict] = []
    predefined_req = iam_client.roles().list(view="FULL")
    while predefined_req is not None:
        resp = predefined_req.execute()
        roles.extend(resp.get("roles", []))
        predefined_req = iam_client.roles().list_next(predefined_req, resp)
    return roles


@timeit
def get_gcp_roles(iam_client: Resource, project_id: str) -> List[Dict]:
    """
    Retrieve custom and predefined roles from GCP for a given project.

    :param iam_client: The IAM resource object created by googleapiclient.discovery.build().
    :param project_id: The GCP Project ID to retrieve roles from.
    :return: A list of dictionaries representing GCP roles.
    """
    roles = []

    # Get custom roles
    custom_req = iam_client.projects().roles().list(parent=f"projects/{project_id}")
    while custom_req is not None:
        resp = custom_req.execute()
        roles.extend(resp.get("roles", []))
        custom_req = iam_client.projects().roles().list_next(custom_req, resp)

    # Get predefined roles (global, not project-specific)
    roles.extend(get_gcp_predefined_roles(iam_client))

    return roles


def transform_gcp_service_accounts(
    raw_accounts: List[Dict[str, Any]],
    project_id: str,
) -> List[Dict[str, Any]]:
    """
    Transform raw GCP service accounts into loader-friendly dicts.
    """
    result: List[Dict[str, Any]] = []
    for sa in raw_accounts:
        result.append(
            {
                "id": sa["uniqueId"],
                "email": sa.get("email"),
                "displayName": sa.get("displayName"),
                "oauth2ClientId": sa.get("oauth2ClientId"),
                "uniqueId": sa.get("uniqueId"),
                "disabled": sa.get("disabled", False),
                "projectId": project_id,
            },
        )
    return result


@timeit
def load_gcp_service_accounts(
    neo4j_session: neo4j.Session,
    service_accounts: List[Dict[str, Any]],
    project_id: str,
    gcp_update_tag: int,
) -> None:
    """
    Load GCP service account data into Neo4j.
    """
    logger.debug(
        f"Loading {len(service_accounts)} service accounts for project {project_id}"
    )

    load(
        neo4j_session,
        GCPServiceAccountSchema(),
        service_accounts,
        lastupdated=gcp_update_tag,
        projectId=project_id,
    )


def transform_gcp_roles(
    raw_roles: List[Dict[str, Any]],
    project_id: str,
) -> List[Dict[str, Any]]:
    """
    Transform raw GCP roles into loader-friendly dicts.
    """
    result: List[Dict[str, Any]] = []
    for role in raw_roles:
        role_name = role["name"]
        if role_name.startswith("roles/"):
            role_type = (
                "BASIC"
                if role_name in ["roles/owner", "roles/editor", "roles/viewer"]
                else "PREDEFINED"
            )
        else:
            role_type = "CUSTOM"

        result.append(
            {
                "id": role_name,
                "name": role_name,
                "title": role.get("title"),
                "description": role.get("description"),
                "deleted": role.get("deleted", False),
                "etag": role.get("etag"),
                "includedPermissions": role.get("includedPermissions", []),
                "roleType": role_type,
                "projectId": project_id,
            },
        )
    return result


@timeit
def load_gcp_roles(
    neo4j_session: neo4j.Session,
    roles: List[Dict[str, Any]],
    project_id: str,
    gcp_update_tag: int,
) -> None:
    """
    Load GCP role data into Neo4j.
    """
    logger.debug(f"Loading {len(roles)} roles for project {project_id}")

    load(
        neo4j_session,
        GCPRoleSchema(),
        roles,
        lastupdated=gcp_update_tag,
        projectId=project_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: Dict[str, Any]
) -> None:
    """
    Run cleanup jobs for GCP IAM data in Neo4j.

    :param neo4j_session: The Neo4j session.
    :param common_job_parameters: Common job parameters for cleanup.
    """
    logger.debug("Running GCP IAM cleanup job")
    job_params = {
        **common_job_parameters,
        "projectId": common_job_parameters.get("PROJECT_ID"),
    }

    cleanup_jobs = [
        GraphJob.from_node_schema(GCPServiceAccountSchema(), job_params),
        GraphJob.from_node_schema(GCPRoleSchema(), job_params),
    ]

    for cleanup_job in cleanup_jobs:
        cleanup_job.run(neo4j_session)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    iam_client: Resource,
    project_id: str,
    gcp_update_tag: int,
    common_job_parameters: Dict[str, Any],
) -> None:
    """
    Sync GCP IAM resources for a given project.

    :param neo4j_session: The Neo4j session.
    :param iam_client: The IAM resource object created by googleapiclient.discovery.build().
    :param project_id: The GCP Project ID to sync.
    :param gcp_update_tag: The timestamp of the current sync run.
    :param common_job_parameters: Common job parameters for the sync.
    """
    logger.info(f"Syncing GCP IAM for project {project_id}")

    service_accounts_raw = get_gcp_service_accounts(iam_client, project_id)
    logger.info(
        f"Found {len(service_accounts_raw)} service accounts in project {project_id}"
    )
    service_accounts = transform_gcp_service_accounts(service_accounts_raw, project_id)
    load_gcp_service_accounts(
        neo4j_session, service_accounts, project_id, gcp_update_tag
    )

    roles_raw = get_gcp_roles(iam_client, project_id)
    logger.info(f"Found {len(roles_raw)} roles in project {project_id}")
    roles = transform_gcp_roles(roles_raw, project_id)
    load_gcp_roles(neo4j_session, roles, project_id, gcp_update_tag)

    # Run cleanup
    cleanup(neo4j_session, common_job_parameters)
