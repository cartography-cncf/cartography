import logging
from typing import Any, Dict, List

import googleapiclient.discovery
import neo4j
from googleapiclient.discovery import Resource

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.gcp.iam import GCPUserSchema, GCPServiceAccountSchema, GCPRoleSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

# GCP API can be subject to rate limiting, so add small delays between calls
LIST_SLEEP = 1
DESCRIBE_SLEEP = 1


@timeit
def get_gcp_users(iam_client: Resource, project_id: str) -> List[Dict[str, Any]]:
    """
    Returns a list of GCP IAM users within the given project.

    :type iam_client: The GCP IAM resource object
    :param iam_client: The IAM resource object created by googleapiclient.discovery.build()

    :type project_id: str
    :param project_id: The GCP Project ID that you are retrieving users from

    :rtype: List[Dict]
    :return: List of GCP IAM users
    """
    users: List[Dict[str, Any]] = []
    try:
        request = iam_client.users().list(parent=f'projects/{project_id}')
        while request is not None:
            response = request.execute()
            if 'users' in response:
                users.extend(response['users'])
            request = iam_client.users().list_next(previous_request=request, previous_response=response)
    except Exception as e:
        logger.warning(f"Error retrieving IAM users for project {project_id}: {e}")
    return users


@timeit
def get_gcp_service_accounts(iam_client: Resource, project_id: str) -> List[Dict[str, Any]]:
    """
    Returns a list of GCP service accounts within the given project.

    :type iam_client: The GCP IAM resource object
    :param iam_client: The IAM resource object created by googleapiclient.discovery.build()

    :type project_id: str
    :param project_id: The GCP Project ID that you are retrieving service accounts from

    :rtype: List[Dict]
    :return: List of GCP service accounts
    """
    service_accounts: List[Dict[str, Any]] = []
    try:
        request = iam_client.projects().serviceAccounts().list(name=f'projects/{project_id}')
        while request is not None:
            response = request.execute()
            if 'accounts' in response:
                service_accounts.extend(response['accounts'])
            request = iam_client.projects().serviceAccounts().list_next(
                previous_request=request,
                previous_response=response,
            )
    except Exception as e:
        logger.warning(f"Error retrieving service accounts for project {project_id}: {e}")
    return service_accounts


@timeit
def get_gcp_roles(iam_client: Resource, project_id: str) -> List[Dict[str, Any]]:
    """
    Returns a list of GCP IAM roles within the given project.

    :type iam_client: The GCP IAM resource object
    :param iam_client: The IAM resource object created by googleapiclient.discovery.build()

    :type project_id: str
    :param project_id: The GCP Project ID that you are retrieving roles from

    :rtype: List[Dict]
    :return: List of GCP IAM roles
    """
    roles: List[Dict[str, Any]] = []
    try:
        request = iam_client.roles().list(parent=f'projects/{project_id}')
        while request is not None:
            response = request.execute()
            if 'roles' in response:
                roles.extend(response['roles'])
            request = iam_client.roles().list_next(previous_request=request, previous_response=response)
    except Exception as e:
        logger.warning(f"Error retrieving IAM roles for project {project_id}: {e}")
    return roles


@timeit
def load_gcp_users(
    neo4j_session: neo4j.Session,
    user_data: List[Dict[str, Any]],
    project_id: str,
    gcp_update_tag: int,
) -> None:
    """
    Ingest GCP IAM users into Neo4j.

    :type neo4j_session: Neo4j session object
    :param neo4j_session: The Neo4j session

    :type user_data: List[Dict]
    :param user_data: A list of GCP IAM users

    :type project_id: str
    :param project_id: The project ID that the users belong to

    :type gcp_update_tag: int
    :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with

    :rtype: None
    :return: Nothing
    """
    logger.info(f"Loading {len(user_data)} GCP users for project {project_id}")
    load(
        neo4j_session,
        GCPUserSchema(),
        user_data,
        lastupdated=gcp_update_tag,
        projectId=project_id,
    )


@timeit
def load_gcp_service_accounts(
    neo4j_session: neo4j.Session,
    service_account_data: List[Dict[str, Any]],
    project_id: str,
    gcp_update_tag: int,
) -> None:
    """
    Ingest GCP service accounts into Neo4j.

    :type neo4j_session: Neo4j session object
    :param neo4j_session: The Neo4j session

    :type service_account_data: List[Dict]
    :param service_account_data: A list of GCP service accounts

    :type project_id: str
    :param project_id: The project ID that the service accounts belong to

    :type gcp_update_tag: int
    :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with

    :rtype: None
    :return: Nothing
    """
    logger.info(f"Loading {len(service_account_data)} GCP service accounts for project {project_id}")
    load(
        neo4j_session,
        GCPServiceAccountSchema(),
        service_account_data,
        lastupdated=gcp_update_tag,
        projectId=project_id,
    )


@timeit
def load_gcp_roles(
    neo4j_session: neo4j.Session,
    role_data: List[Dict[str, Any]],
    project_id: str,
    gcp_update_tag: int,
) -> None:
    """
    Ingest GCP IAM roles into Neo4j.

    :type neo4j_session: Neo4j session object
    :param neo4j_session: The Neo4j session

    :type role_data: List[Dict]
    :param role_data: A list of GCP IAM roles

    :type project_id: str
    :param project_id: The project ID that the roles belong to

    :type gcp_update_tag: int
    :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with

    :rtype: None
    :return: Nothing
    """
    logger.info(f"Loading {len(role_data)} GCP roles for project {project_id}")
    load(
        neo4j_session,
        GCPRoleSchema(),
        role_data,
        lastupdated=gcp_update_tag,
        projectId=project_id,
    )


@timeit
def cleanup(neo4j_session: neo4j.Session, common_job_parameters: Dict[str, Any]) -> None:
    logger.debug("Running GCP IAM cleanup job")
    cleanup_jobs = [
        GraphJob.from_node_schema(GCPUserSchema(), common_job_parameters),
        GraphJob.from_node_schema(GCPServiceAccountSchema(), common_job_parameters),
        GraphJob.from_node_schema(GCPRoleSchema(), common_job_parameters),
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
    Sync GCP IAM resources (users, service accounts, and roles) for a given project.

    :type neo4j_session: Neo4j session object
    :param neo4j_session: The Neo4j session

    :type iam_client: The GCP IAM resource object
    :param iam_client: The IAM resource object created by googleapiclient.discovery.build()

    :type project_id: str
    :param project_id: The project ID to sync

    :type gcp_update_tag: int
    :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with

    :type common_job_parameters: Dict
    :param common_job_parameters: Dictionary of common parameters used for Neo4j jobs

    :rtype: None
    :return: Nothing
    """
    logger.info(f"Syncing GCP IAM for project {project_id}")
    
    # Get and load users
    users = get_gcp_users(iam_client, project_id)
    load_gcp_users(neo4j_session, users, project_id, gcp_update_tag)
    
    # Get and load service accounts
    service_accounts = get_gcp_service_accounts(iam_client, project_id)
    load_gcp_service_accounts(neo4j_session, service_accounts, project_id, gcp_update_tag)
    
    # Get and load roles
    roles = get_gcp_roles(iam_client, project_id)
    load_gcp_roles(neo4j_session, roles, project_id, gcp_update_tag)
    
    # Run cleanup
    cleanup(neo4j_session, common_job_parameters) 