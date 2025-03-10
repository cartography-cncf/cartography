import logging
from enum import Enum
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

import neo4j
from googleapiclient.discovery import Resource

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.gcp.iam import GCPRoleSchema
from cartography.models.gcp.iam import GCPServiceAccountSchema
from cartography.util import timeit


class ParentType(Enum):
    PROJECT = 'projects'
    ORGANIZATION = 'organizations'


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
def get_gcp_roles(iam_client: Resource, parent_id: str, parent_type: ParentType = ParentType.PROJECT) -> List[Dict]:
    """
    Retrieve roles from GCP for a given parent (project or organization). Folders do not have custom roles.
    For organizations, this includes predefined roles and custom org-level roles.
    For projects, this includes custom project-level roles.

    :param iam_client: The IAM resource object
    :param parent_id: The GCP Project ID or Organization ID
    :param parent_type: ParentType enum specifying whether this is a project or organization
    :return: List of role dictionaries
    """
    try:
        roles = []
        parent_path = f'{parent_type.value}/{parent_id}'

        # Get custom roles for the parent (project or organization)
        custom_roles = (
            iam_client.projects().roles().list(parent=parent_path, view='FULL')
            if parent_type == ParentType.PROJECT
            else iam_client.organizations().roles().list(parent=parent_path, view='FULL')
        )

        while custom_roles is not None:
            resp = custom_roles.execute()
            roles.extend(resp.get('roles', []))
            custom_roles = (
                iam_client.projects().roles().list_next(custom_roles, resp)
                if parent_type == ParentType.PROJECT
                else iam_client.organizations().roles().list_next(custom_roles, resp)
            )

        # Get predefined and basic roles (only when syncing organization)
        if parent_type == ParentType.ORGANIZATION:
            predefined_roles = iam_client.roles().list(view='FULL')
            while predefined_roles is not None:
                resp = predefined_roles.execute()
                roles.extend(resp.get('roles', []))
                predefined_roles = iam_client.roles().list_next(predefined_roles, resp)

        return roles
    except Exception:
        logger.error(
            "Error getting GCP roles for %s/%s",
            parent_type.value,
            parent_id,
            exc_info=True,
        )
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
    )


@timeit
def load_gcp_roles(
    neo4j_session: neo4j.Session,
    roles: List[Dict],
    parent_id: str,
    parent_type: ParentType,
    gcp_update_tag: int,
    job_parameters: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Load GCP role data into Neo4j.

    For organization-level roles, parent_id is taken as the organization identifier.
    For project-level roles, if job_parameters is provided and contains an 'ORGANIZATION_ID' value,
    that value will be used. This way, the caller does not need to pass a separate organization_id.
    """
    logger.debug("Loading %d roles for %s/%s", len(roles), parent_type.value, parent_id)
    transformed_roles = []

    if job_parameters is None:
        job_parameters = {}

    if parent_type == ParentType.PROJECT:
        # For project roles, try to derive the organization id from job_parameters.
        org_id = job_parameters.get('ORGANIZATION_ID', '')
    else:
        org_id = parent_id if parent_id.startswith('organizations/') else f"organizations/{parent_id}"

    for role in roles:
        role_name = role['name']

        # For project sync, only process roles that strictly belong to the project.
        if parent_type == ParentType.PROJECT and not role_name.startswith(f'projects/{parent_id}/roles/'):
            continue

        if role_name.startswith('roles/'):
            if role_name in ['roles/owner', 'roles/editor', 'roles/viewer']:
                role_type = 'BASIC'
            else:
                role_type = 'PREDEFINED'
            scope = 'GLOBAL'
        else:
            role_type = 'CUSTOM'
            scope = parent_type.value.upper().rstrip('S')

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
            'organization_id': org_id,
        }
        transformed_roles.append(transformed_role)

    load_kwargs = {
        'lastupdated': gcp_update_tag,
        'organizationId': org_id,
    }
    if parent_type == ParentType.PROJECT:
        load_kwargs['projectId'] = parent_id
    else:
        load_kwargs['projectId'] = ''

    logger.debug(f'Loading roles with kwargs: {load_kwargs}')

    load(
        neo4j_session,
        GCPRoleSchema(),
        transformed_roles,
        **load_kwargs,
    )


@timeit
def cleanup(neo4j_session: neo4j.Session, common_job_parameters: Dict[str, Any], parent_type: ParentType) -> None:
    """
    Run cleanup jobs for GCP IAM data in Neo4j.

    :param neo4j_session: The Neo4j session
    :param common_job_parameters: Common parameters for cleanup jobs
    :param parent_type: ParentType enum specifying whether this is a project or organization cleanup
    """
    logger.debug("Running GCP IAM cleanup job for %s", parent_type.value)

    cleanup_jobs = []
    cleanup_job_params = {
        **common_job_parameters,
        'projectId': common_job_parameters.get('PROJECT_ID'),
        'organizationId': common_job_parameters.get('ORGANIZATION_ID'),
    }

    # Only include service account cleanup for project-level syncs
    if parent_type == ParentType.PROJECT:
        cleanup_jobs.append(GraphJob.from_node_schema(GCPServiceAccountSchema(), cleanup_job_params))

    cleanup_jobs.append(GraphJob.from_node_schema(GCPRoleSchema(), cleanup_job_params))

    for cleanup_job in cleanup_jobs:
        cleanup_job.run(neo4j_session)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    iam_client: Resource,
    parent_id: str,
    parent_type: ParentType,
    gcp_update_tag: int,
    common_job_parameters: Dict[str, Any],
) -> None:
    """
    Sync GCP IAM resources for a given parent (project or organization).

    :param neo4j_session: The Neo4j session
    :param iam_client: The IAM resource object
    :param parent_id: The GCP Project ID or Organization ID
    :param parent_type: ParentType enum specifying whether this is a project or organization
    :param gcp_update_tag: The timestamp for this sync run
    :param common_job_parameters: Common parameters for sync jobs
    """
    logger.info("Syncing GCP IAM for %s/%s", parent_type.value, parent_id)

    # Get and load service accounts (only for projects)
    if parent_type == ParentType.PROJECT:
        service_accounts = get_gcp_service_accounts(iam_client, parent_id)
        logger.info("Found %d service accounts in project %s", len(service_accounts), parent_id)
        load_gcp_service_accounts(neo4j_session, service_accounts, parent_id, gcp_update_tag)

    roles = get_gcp_roles(iam_client, parent_id, parent_type)
    logger.info("Found %d roles in %s/%s", len(roles), parent_type.value, parent_id)

    # Pass the common_job_parameters directly.
    load_gcp_roles(neo4j_session, roles, parent_id, parent_type, gcp_update_tag, common_job_parameters)

    cleanup(neo4j_session, common_job_parameters, parent_type)
