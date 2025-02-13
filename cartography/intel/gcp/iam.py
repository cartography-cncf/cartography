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
def get_gcp_service_accounts(iam_client: Resource, project_id: str) -> List[Dict[str, Any]]:
    """
    Retrieve a list of GCP service accounts for a given project.

    :param iam_client: The IAM resource object created by googleapiclient.discovery.build().
    :param project_id: The GCP Project ID to retrieve service accounts from.
    :return: A list of dictionaries representing GCP service accounts.
    """
    service_accounts: List[Dict[str, Any]] = []
    try:
        request = iam_client.projects().serviceAccounts().list(
            name=f'projects/{project_id}',
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
def get_gcp_roles(iam_client: Resource, parent_id: str, parent_type: str = 'projects') -> List[Dict]:
    """
    Retrieve roles from GCP for a given parent (project or organization). Folders do not have custom roles.
    For organizations, this includes predefined roles and custom org-level roles.
    For projects, this includes custom project-level roles.

    :param iam_client: The IAM resource object
    :param parent_id: The GCP Project ID or Organization ID
    :param parent_type: Either 'projects' or 'organizations'
    :return: List of role dictionaries
    """
    try:
        roles = []
        parent_path = f'{parent_type}/{parent_id}'

        # Get custom roles for the parent (project or organization)
        custom_roles = iam_client.projects().roles().list(parent=parent_path) if parent_type == 'projects' else \
                       iam_client.organizations().roles().list(parent=parent_path)
        
        while custom_roles is not None:
            resp = custom_roles.execute()
            roles.extend(resp.get('roles', []))
            custom_roles = iam_client.projects().roles().list_next(custom_roles, resp) if parent_type == 'projects' else \
                           iam_client.organizations().roles().list_next(custom_roles, resp)

        # Get predefined and basic roles (only when syncing organization)
        if parent_type == 'organizations':
            predefined_req = iam_client.roles().list(view='FULL')
            while predefined_req is not None:
                resp = predefined_req.execute()
                roles.extend(resp.get('roles', []))
                predefined_req = iam_client.roles().list_next(predefined_req, resp)

        return roles
    except Exception as e:
        print(f"Error getting GCP roles for {parent_type}/{parent_id} - {e}")
        return []


@timeit
def load_gcp_service_accounts(
    neo4j_session: neo4j.Session,
    service_accounts: List[Dict[str, Any]],
    project_id: str,
    gcp_update_tag: int,
) -> None:
    """
    Load GCP service account data into Neo4j.

    :param neo4j_session: The Neo4j session.
    :param service_accounts: A list of service account data to load.
    :param project_id: The GCP Project ID associated with the service accounts.
    :param gcp_update_tag: The timestamp of the current sync run.
    """
    logger.debug(f"Loading {len(service_accounts)} service accounts for project {project_id}")
    transformed_service_accounts = []
    for sa in service_accounts:
        transformed_sa = {
            'id': sa['uniqueId'],
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
        additional_labels=['GCPPrincipal'],
    )


@timeit
def load_gcp_roles(
    neo4j_session: neo4j.Session,
    roles: List[Dict],
    parent_id: str,
    parent_type: str,
    gcp_update_tag: int,
) -> None:
    """
    Load GCP role data into Neo4j.
    """
    logger.debug(f"Loading {len(roles)} roles for {parent_type}/{parent_id}")
    transformed_roles = []
    
    for role in roles:
        role_name = role['name']
        if role_name.startswith('roles/'):
            if role_name in ['roles/owner', 'roles/editor', 'roles/viewer']:
                role_type = 'BASIC'
            else:
                role_type = 'PREDEFINED'
            scope = 'GLOBAL'
        else:
            role_type = 'CUSTOM'
            scope = parent_type.upper().rstrip('S')  # Keep the scope logic

        transformed_role = {
            'id': role_name,
            'name': role_name,
            'title': role.get('title'),
            'description': role.get('description'),
            'deleted': role.get('deleted', False),
            'etag': role.get('etag'),
            'includedPermissions': role.get('includedPermissions', []),
            'roleType': role_type,
            'scope': scope,
        }
        transformed_roles.append(transformed_role)

    # Always connect to organization, regardless of scope
    org_id = parent_id if parent_type == 'organizations' else parent_id.split('/')[0]
    load(
        neo4j_session,
        GCPRoleSchema(),
        transformed_roles,
        lastupdated=gcp_update_tag,
        organizationId=f"organizations/{org_id}",
    )


@timeit
def cleanup(neo4j_session: neo4j.Session, common_job_parameters: Dict[str, Any], parent_type: str) -> None:
    """
    Run cleanup jobs for GCP IAM data in Neo4j.
    """
    logger.debug("Running GCP IAM cleanup job")

    cleanup_jobs = []
    
    # Service account cleanup needs projectId
    if parent_type == 'projects':
        sa_job_params = {
            **common_job_parameters,
            'projectId': common_job_parameters.get('PROJECT_ID'),
        }
        cleanup_jobs.append(GraphJob.from_node_schema(GCPServiceAccountSchema(), sa_job_params))
    
    # Role cleanup always needs organizationId since all roles connect to org
    role_job_params = {
        **common_job_parameters,
        'organizationId': common_job_parameters.get('ORGANIZATION_ID'),
    }
    cleanup_jobs.append(GraphJob.from_node_schema(GCPRoleSchema(), role_job_params))

    for cleanup_job in cleanup_jobs:
        cleanup_job.run(neo4j_session)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    iam_client: Resource,
    parent_id: str,
    parent_type: str,
    gcp_update_tag: int,
    common_job_parameters: Dict[str, Any],
) -> None:
    """
    Sync GCP IAM resources for a given parent (project or organization).
    """
    logger.info(f"Syncing GCP IAM for {parent_type}/{parent_id}")

    # Get and load roles
    roles = get_gcp_roles(iam_client, parent_id, parent_type)
    logger.info(f"Found {len(roles)} roles in {parent_type}/{parent_id}")
    load_gcp_roles(neo4j_session, roles, parent_id, parent_type, gcp_update_tag)

    # Run cleanup with parent type
    cleanup(neo4j_session, common_job_parameters, parent_type)
