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
        request = iam_client.projects().serviceAccounts().list(
            name=f'projects/{project_id}'
        )
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
        request = iam_client.roles().list(
            parent=f'projects/{project_id}'
        )
        while request is not None:
            response = request.execute()
            if 'roles' in response:
                roles.extend(response['roles'])
            request = iam_client.roles().list_next(
                previous_request=request,
                previous_response=response,
            )
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
    service_accounts: List[Dict[str, Any]],
    project_id: str,
    gcp_update_tag: int,
) -> None:
    """
    Load GCP service account information into Neo4j.
    """
    logger.debug(f"Loading {len(service_accounts)} service accounts for project {project_id}")
    transformed_service_accounts = []
    for sa in service_accounts:
        transformed_sa = {
            'id': sa['uniqueId'],  # Use uniqueId as the id field
            'email': sa.get('email'),
            'displayName': sa.get('displayName'),
            'oauth2ClientId': sa.get('oauth2ClientId'),
            'uniqueId': sa.get('uniqueId'),
            'disabled': sa.get('disabled', False),
            'projectId': project_id,
        }
        transformed_service_accounts.append(transformed_sa)
    
    load(
        neo4j_session,
        GCPServiceAccountSchema(),
        transformed_service_accounts,
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
    """
    Delete nodes that are no longer present in GCP
    """
    logger.debug("Running GCP IAM cleanup job")
    # Add projectId to the job parameters
    job_params = {
        **common_job_parameters,
        'projectId': common_job_parameters.get('PROJECT_ID'),
    }
    
    cleanup_jobs = [
        GraphJob.from_node_schema(GCPUserSchema(), job_params),
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
    Sync GCP IAM resources (service accounts and roles) for a given project.
    """
    logger.info(f"Syncing GCP IAM for project {project_id}")
    
    # Get and load service accounts
    service_accounts = get_gcp_service_accounts(iam_client, project_id)
    logger.info(f"Found {len(service_accounts)} service accounts in project {project_id}")
    load_gcp_service_accounts(neo4j_session, service_accounts, project_id, gcp_update_tag)
    
    # Get and load roles
    roles = get_gcp_roles(iam_client, project_id)
    logger.info(f"Found {len(roles)} roles in project {project_id}")
    load_gcp_roles(neo4j_session, roles, project_id, gcp_update_tag)
    
    # Run cleanup
    cleanup(neo4j_session, common_job_parameters) 