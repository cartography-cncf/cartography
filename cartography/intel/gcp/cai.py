import logging
import time
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

# Maximum number of retries for Google API requests (handles transient errors and rate limiting)
GOOGLE_API_NUM_RETRIES = 5
# Delay between CAI API calls to avoid hitting rate limits (100 requests/min per project)
CAI_CALL_DELAY_SECONDS = 1


@timeit
def get_gcp_service_accounts_cai(
    cai_client: Resource, project_id: str
) -> List[Dict[str, Any]]:
    """
    Retrieve a list of GCP service accounts using Cloud Asset Inventory API.

    :param cai_client: The Cloud Asset Inventory resource object created by googleapiclient.discovery.build().
    :param project_id: The GCP Project ID to retrieve service accounts from.
    :return: A list of dictionaries representing GCP service accounts.
    """
    service_accounts: List[Dict[str, Any]] = []
    request = cai_client.assets().list(
        parent=f"projects/{project_id}",
        assetTypes=["iam.googleapis.com/ServiceAccount"],
        contentType="RESOURCE",  # Request full resource data, not just metadata
    )
    while request is not None:
        response = request.execute(num_retries=GOOGLE_API_NUM_RETRIES)
        if "assets" in response:
            # Extract the actual service account data from CAI response
            for asset in response["assets"]:
                if "resource" in asset and "data" in asset["resource"]:
                    service_accounts.append(asset["resource"]["data"])
        request = cai_client.assets().list_next(
            previous_request=request,
            previous_response=response,
        )
        # Add delay between paginated requests to avoid rate limiting
        if request is not None:
            time.sleep(CAI_CALL_DELAY_SECONDS)
    return service_accounts


@timeit
def get_gcp_roles_cai(cai_client: Resource, project_id: str) -> List[Dict]:
    """
    Retrieve custom roles from GCP using Cloud Asset Inventory API.

    Note: This only returns custom roles defined at the project level.
    Predefined roles are global and cannot be retrieved via CAI.
    Use the `predefined_roles` parameter in the `sync` function to include them.

    :param cai_client: The Cloud Asset Inventory resource object created by googleapiclient.discovery.build().
    :param project_id: The GCP Project ID to retrieve roles from.
    :return: A list of dictionaries representing GCP custom roles.
    """
    roles = []

    # Get custom roles (project-level)
    custom_request = cai_client.assets().list(
        parent=f"projects/{project_id}",
        assetTypes=["iam.googleapis.com/Role"],
        contentType="RESOURCE",  # Request full resource data, not just metadata
    )
    while custom_request is not None:
        resp = custom_request.execute(num_retries=GOOGLE_API_NUM_RETRIES)
        if "assets" in resp:
            for asset in resp["assets"]:
                if "resource" in asset and "data" in asset["resource"]:
                    roles.append(asset["resource"]["data"])
        custom_request = cai_client.assets().list_next(custom_request, resp)
        # Add delay between paginated requests to avoid rate limiting
        if custom_request is not None:
            time.sleep(CAI_CALL_DELAY_SECONDS)

    return roles


def transform_gcp_service_accounts_cai(
    raw_accounts: List[Dict[str, Any]],
    project_id: str,
) -> List[Dict[str, Any]]:
    """
    Transform raw GCP service accounts from CAI into loader-friendly dicts.

    :param raw_accounts: List of service account dicts from CAI API.
    :param project_id: The GCP Project ID these service accounts belong to.
    :return: List of transformed service account dicts ready for loading.
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


def transform_gcp_roles_cai(
    raw_roles: List[Dict[str, Any]],
    project_id: str,
) -> List[Dict[str, Any]]:
    """
    Transform raw GCP roles from CAI into loader-friendly dicts.

    :param raw_roles: List of role dicts from CAI API.
    :param project_id: The GCP Project ID these roles belong to.
    :return: List of transformed role dicts ready for loading.
    """
    result: List[Dict[str, Any]] = []
    for role in raw_roles:
        role_name = role["name"]
        if role_name.startswith("roles/"):
            # CAI currently does not return global predefined roles; keep branch for parity/future support
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
def load_gcp_service_accounts_cai(
    neo4j_session: neo4j.Session,
    service_accounts: List[Dict[str, Any]],
    project_id: str,
    gcp_update_tag: int,
) -> None:
    """
    Load GCP service account data into Neo4j using CAI-sourced data.

    :param neo4j_session: The Neo4j session.
    :param service_accounts: List of transformed service account dicts.
    :param project_id: The GCP Project ID.
    :param gcp_update_tag: The timestamp of the current sync run.
    """
    logger.debug(
        f"Loading {len(service_accounts)} service accounts for project {project_id} via CAI"
    )

    load(
        neo4j_session,
        GCPServiceAccountSchema(),
        service_accounts,
        lastupdated=gcp_update_tag,
        projectId=project_id,
    )


@timeit
def load_gcp_roles_cai(
    neo4j_session: neo4j.Session,
    roles: List[Dict[str, Any]],
    project_id: str,
    gcp_update_tag: int,
) -> None:
    """
    Load GCP role data into Neo4j using CAI-sourced data.

    :param neo4j_session: The Neo4j session.
    :param roles: List of transformed role dicts.
    :param project_id: The GCP Project ID.
    :param gcp_update_tag: The timestamp of the current sync run.
    """
    logger.debug(f"Loading {len(roles)} roles for project {project_id} via CAI")

    load(
        neo4j_session,
        GCPRoleSchema(),
        roles,
        lastupdated=gcp_update_tag,
        projectId=project_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    project_id: str,
    common_job_parameters: Dict[str, Any],
) -> None:
    """
    Run cleanup jobs for GCP IAM data in Neo4j.

    :param neo4j_session: The Neo4j session.
    :param project_id: The GCP Project ID to clean up resources for.
    :param common_job_parameters: Common job parameters for cleanup.
    """
    logger.debug(f"Running GCP IAM cleanup job (CAI) for project {project_id}")
    job_params = {
        **common_job_parameters,
        "projectId": project_id,
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
    cai_client: Resource,
    project_id: str,
    gcp_update_tag: int,
    common_job_parameters: Dict[str, Any],
    predefined_roles: List[Dict[str, Any]] | None = None,
) -> None:
    """
    Sync GCP IAM resources for a given project using Cloud Asset Inventory API.

    :param neo4j_session: The Neo4j session.
    :param cai_client: The Cloud Asset Inventory resource object created by googleapiclient.discovery.build().
    :param project_id: The GCP Project ID to sync.
    :param gcp_update_tag: The timestamp of the current sync run.
    :param common_job_parameters: Common job parameters for the sync.
    :param predefined_roles: Optional list of predefined roles fetched from the IAM API.
        Since predefined roles are global (not project-specific), they can be fetched once
        and reused across all target projects.
    """
    logger.info(f"Syncing GCP IAM for project {project_id} via Cloud Asset Inventory")

    service_accounts_raw = get_gcp_service_accounts_cai(cai_client, project_id)
    logger.info(
        f"Found {len(service_accounts_raw)} service accounts in project {project_id} via CAI"
    )
    service_accounts = transform_gcp_service_accounts_cai(
        service_accounts_raw, project_id
    )
    load_gcp_service_accounts_cai(
        neo4j_session, service_accounts, project_id, gcp_update_tag
    )

    # Add delay between API calls to avoid rate limiting
    time.sleep(CAI_CALL_DELAY_SECONDS)

    # Get custom roles from CAI
    roles_raw = get_gcp_roles_cai(cai_client, project_id)
    logger.info(f"Found {len(roles_raw)} custom roles in project {project_id} via CAI")

    # Merge with predefined roles if provided (fetched once from IAM API and reused)
    if predefined_roles:
        roles_raw.extend(predefined_roles)
        logger.info(f"Added {len(predefined_roles)} predefined roles from IAM API")

    roles = transform_gcp_roles_cai(roles_raw, project_id)
    load_gcp_roles_cai(neo4j_session, roles, project_id, gcp_update_tag)

    # Run cleanup
    cleanup(neo4j_session, project_id, common_job_parameters)
