import logging
from typing import Any, Dict, List

import googleapiclient.discovery
import neo4j
from googleapiclient.discovery import Resource

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.gcp.iam import GCPServiceAccountSchema, GCPRoleSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

# GCP API can be subject to rate limiting, so add small delays between calls
LIST_SLEEP = 1
DESCRIBE_SLEEP = 1


@timeit
def get_gcp_service_accounts(iam_client: Resource, project_id: str) -> List[Dict[str, Any]]:
    """
    Returns a list of GCP service accounts within the given project.

    :param iam_client: The IAM resource object created by googleapiclient.discovery.build()
    :param project_id: The GCP Project ID that you are retrieving service accounts from

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
def get_gcp_roles(iam_client: Resource, project_id: str) -> List[Dict]:
    """
    Get both custom and predefined roles from GCP.

    :param iam_client: The IAM resource object created by googleapiclient.discovery.build()
    :param project_id: The project ID number to sync.
    See https://googleapis.github.io/google-api-python-client/docs/epy/googleapiclient.discovery-module.html#build.
    
    :return: List of custom and predefined roles.
    """
    try:
        roles = []
        
        # Get custom roles
        custom_req = iam_client.projects().roles().list(parent=f'projects/{project_id}')
        while custom_req is not None:
            resp = custom_req.execute()
            roles.extend(resp.get('roles', []))
            custom_req = iam_client.projects().roles().list_next(custom_req, resp)
            
        # Get predefined roles
        predefined_req = iam_client.roles().list(view='FULL')
        while predefined_req is not None:
            resp = predefined_req.execute()
            roles.extend(resp.get('roles', []))
            predefined_req = iam_client.roles().list_next(predefined_req, resp)
            
        return roles
    except Exception as e:
        logger.warning("Error getting GCP roles - {}".format(e))
        return []


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
    roles: List[Dict[str, Any]],
    project_id: str,
    gcp_update_tag: int,
) -> None:
    """
    Load GCP role information into Neo4j.
    """
    logger.debug(f"Loading {len(roles)} roles for project {project_id}")
    transformed_roles = []
    for role in roles:
        role_name = role['name']
        # Determine role type
        if role_name.startswith('roles/'):
            if role_name in ['roles/owner', 'roles/editor', 'roles/viewer']:
                role_type = 'BASIC'
            else:
                role_type = 'PREDEFINED'
        else:
            role_type = 'CUSTOM'
            
        transformed_role = {
            'id': role_name,
            'name': role_name,
            'title': role.get('title'),
            'description': role.get('description'),
            'deleted': role.get('deleted', False),
            'etag': role.get('etag'),
            'includedPermissions': role.get('includedPermissions', []),
            'roleType': role_type,
            'projectId': project_id,
        }
        transformed_roles.append(transformed_role)
    
    load(
        neo4j_session,
        GCPRoleSchema(),
        transformed_roles,
        lastupdated=gcp_update_tag,
        projectId=project_id,
    )


@timeit
def cleanup(neo4j_session: neo4j.Session, common_job_parameters: Dict[str, Any]) -> None:
    logger.debug("Running GCP IAM cleanup job")
    # Add projectId to the job parameters
    job_params = {
        **common_job_parameters,
        'projectId': common_job_parameters.get('PROJECT_ID'),
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
    Sync GCP IAM resources (service accounts and roles) for a given project.
    Note that "users" in GCP come from the GSuite module. 
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