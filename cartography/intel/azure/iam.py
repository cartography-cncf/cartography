import asyncio
import logging
import math
from datetime import datetime
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Set
from typing import TypedDict
from typing import Union

import neo4j
from azure.core.exceptions import HttpResponseError
from azure.mgmt.authorization import AuthorizationManagementClient
from azure.mgmt.msi import ManagedServiceIdentityClient
from cloudconsolelink.clouds.azure import AzureLinker
from msgraph import GraphServiceClient
from msgraph.generated.groups.groups_request_builder import GroupsRequestBuilder
from msgraph.generated.users.users_request_builder import UsersRequestBuilder

from .util.credentials import Credentials
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)
azure_console_link = AzureLinker()

scopes = ['https://graph.microsoft.com/.default']

# A safe batch size for "in" filters with GUIDs to avoid 414 URI Too Long errors.
# MS Graph URL limit is ~2048 chars. 36-char GUID + quotes/commas = ~39 chars.
# 2048 / 39 = ~52. A batch size of 25 is safe.
SAFE_BATCH_SIZE = 15


def load_tenant_users(session: neo4j.Session, tenant_id: str, data_list: List[Dict], update_tag: int) -> None:
    iteration_size = 500
    total_items = len(data_list)
    total_iterations = math.ceil(len(data_list) / iteration_size)

    for counter in range(0, total_iterations):
        start = iteration_size * (counter)

        if (start + iteration_size) >= total_items:
            end = total_items
            paged_users = data_list[start:]

        else:
            end = start + iteration_size
            paged_users = data_list[start:end]

        session.write_transaction(_load_tenant_users_tx, tenant_id, paged_users, update_tag)

        logger.info(f"Iteration {counter + 1} of {total_iterations}. {start} - {end} - {len(paged_users)}")


def load_roles(session: neo4j.Session, tenant_id: str, data_list: List[Dict], role_assignments_list: List[Dict], update_tag: int, SUBSCRIPTION_ID: str) -> None:
    session.write_transaction(_load_roles_tx, tenant_id, data_list, role_assignments_list, update_tag, SUBSCRIPTION_ID)


def load_managed_identities(session: neo4j.Session, tenant_id: str, data_list: List[Dict], update_tag: int) -> None:
    session.write_transaction(_load_managed_identities_tx, tenant_id, data_list, update_tag)


def load_tenant_groups(session: neo4j.Session, tenant_id: str, data_list: List[Dict], update_tag: int) -> None:
    session.write_transaction(_load_tenant_groups_tx, tenant_id, data_list, update_tag)


def load_tenant_applications(session: neo4j.Session, tenant_id: str, data_list: List[Dict], update_tag: int) -> None:
    session.write_transaction(_load_tenant_applications_tx, tenant_id, data_list, update_tag)


def load_tenant_service_accounts(
    session: neo4j.Session, tenant_id: str, data_list: List[Dict], update_tag: int,
) -> None:
    session.write_transaction(_load_tenant_service_accounts_tx, tenant_id, data_list, update_tag)


def load_tenant_domains(session: neo4j.Session, tenant_id: str, data_list: List[Dict], update_tag: int) -> None:
    session.write_transaction(_load_tenant_domains_tx, tenant_id, data_list, update_tag)


def set_used_state(session: neo4j.Session, tenant_id: str, common_job_parameters: Dict, update_tag: int) -> None:
    session.write_transaction(_set_used_state_tx, tenant_id, common_job_parameters, update_tag)


@timeit
def get_graph_client(credentials: Credentials, tenant_id: Optional[str] = None) -> GraphServiceClient:
    """
    Create a Microsoft Graph client.
    This replaces the deprecated Azure AD Graph client.
    """
    client = GraphServiceClient(credentials, scopes)
    return client


@timeit
def get_default_graph_client(credentials: Credentials) -> GraphServiceClient:
    """
    Create a Microsoft Graph client - maintained for backward compatibility.
    This replaces the deprecated Azure AD Graph client (GraphRbacManagementClient)
    which Microsoft is retiring by June 30, 2025.

    Microsoft Graph API documentation: https://learn.microsoft.com/en-us/graph/use-the-api
    """
    return get_graph_client(credentials)


@timeit
def get_authorization_client(credentials: Credentials, subscription_id: str) -> AuthorizationManagementClient:
    client = AuthorizationManagementClient(credentials, subscription_id)
    return client


@timeit
def get_managed_identity_client(credentials: Credentials, subscription_id: str) -> ManagedServiceIdentityClient:
    client = ManagedServiceIdentityClient(credentials, subscription_id)
    return client


@timeit
async def list_tenant_users(client: GraphServiceClient, tenant_id: str, filter_query: Optional[str] = None) -> List[Dict]:
    """
    List users from Microsoft Graph API.
    Microsoft Graph API documentation: https://learn.microsoft.com/en-us/graph/api/user-list
    """
    try:
        request_config = None
        if filter_query:
            # Use a request configuration to add the $filter query parameter
            query_params = UsersRequestBuilder.UsersRequestBuilderGetQueryParameters(
                filter=filter_query,
            )
            request_config = UsersRequestBuilder.UsersRequestBuilderGetRequestConfiguration(
                query_parameters=query_params,
            )
        users: List[Dict] = []
        response = await client.users.get(request_configuration=request_config)
        if not response or not response.value:
            return []
        users.extend(response.value)

        while response.odata_next_link:
            response = await client.users.with_url(response.odata_next_link).get()
            users.extend(response.value)

        users = transform_users(users, tenant_id)
        return users

    except HttpResponseError as e:
        logger.warning(f"Error while retrieving tenant users - {e}")
        return []


def transform_users(users_list: List[Dict], tenant_id: str) -> List[Dict]:
    """
    User properties documentation: https://learn.microsoft.com/en-us/graph/api/resources/user?view=graph-rest-1.0
    """
    users: List[Dict] = []

    for user in users_list:
        user_id = getattr(user, 'id', None)
        display_name = getattr(user, 'display_name', None)
        user_principal_name = getattr(user, 'user_principal_name', None)
        mail = getattr(user, 'mail', None)
        given_name = getattr(user, 'given_name', None)
        surname = getattr(user, 'surname', None)
        job_title = getattr(user, 'job_title', None)
        mobile_phone = getattr(user, 'mobile_phone', None)
        office_location = getattr(user, 'office_location', None)
        preferred_language = getattr(user, 'preferred_language', None)

        # User account properties
        account_enabled = getattr(user, 'account_enabled', None)
        user_type = getattr(user, 'user_type', None)
        mail_nickname = getattr(user, 'mail_nickname', None)
        usage_location = getattr(user, 'usage_location', None)
        deleted_date_time = getattr(user, 'deleted_date_time', None)
        created_date_time = getattr(user, 'created_date_time', None)

        # Additional properties that might not be available in all responses
        department = getattr(user, 'department', None)
        company_name = getattr(user, 'company_name', None)

        # Custom properties we use internally
        custom_id = f"tenants/{tenant_id}/users/{user_id}"
        consolelink = azure_console_link.get_console_link(id=user_id, iam_entity_type='user')

        # Map to our internal structure
        usr = {
            'id': custom_id,
            'consolelink': consolelink,
            'object_id': user_id,
            'user_principal_name': user_principal_name,
            'email': mail,
            'name': display_name,
            'given_name': given_name,
            'surname': surname,
            'job_title': job_title,
            'user_type': user_type,
            'object_type': 'User',  # Custom property - not from the API
            'mail_nickname': mail_nickname,
            'account_enabled': account_enabled,
            'usage_location': usage_location,
            'deletion_timestamp': deleted_date_time,
            'create_date': created_date_time,
            'company_name': company_name,
            'mobile': mobile_phone,
            'office_location': office_location,
            'preferred_language': preferred_language,
            'department': department,
        }
        users.append(usr)

    return users


def transform_user(user: Dict, tenant_id: str) -> Dict:
    # User properties - https://learn.microsoft.com/en-us/graph/api/resources/user?view=graph-rest-1.0
    return {
        'id': f"tenants/{tenant_id}/users/{user['object_id']}",
        'consolelink': azure_console_link.get_console_link(id=user['object_id'], iam_entity_type='user'),
        'object_id': user['object_id'],
        'user_principal_name': user['user_principal_name'],
        'email': user['mail'],
        'name': user['display_name'],
        'given_name': user['given_name'],
        'surname': user['surname'],
        'user_type': user['user_type'],
        'object_type': user['object_type'],
        'mail_nickname': user['mail_nickname'],
        'account_enabled': user['account_enabled'],
        'usage_location': user['usage_location'],
        'deletion_timestamp': user['deletion_timestamp'],
        'create_date': user['additional_properties']['createdDateTime'],
        'company_name': user['additional_properties']['companyName'],
        'refresh_tokens_valid_from': user['additional_properties']['refreshTokensValidFromDateTime'],
        'mobile': user['additional_properties']['mobile'],
    }


def _load_tenant_users_tx(
    tx: neo4j.Transaction, tenant_id: str, tenant_users_list: List[Dict], update_tag: int,
) -> None:
    ingest_user = """
    UNWIND $tenant_users_list AS user
    MERGE (i:AzureUser{id: user.id})
    ON CREATE SET i:AzurePrincipal,
    i.firstseen = timestamp(),
    i.consolelink = user.consolelink,
    i.object_id = user.object_id,
    i.object_type = user.object_type,
    i.region = $region
    SET i.lastupdated = $update_tag,
    i.consolelink = user.consolelink,
    i.user_principal_name = user.user_principal_name,
    i.email = user.email,
    i.name = user.name,
    i.given_name = user.given_name,
    i.surname = user.surname,
    i.job_title = user.job_title,
    i.user_type = user.user_type,
    i.mail_nickname = user.mail_nickname,
    i.account_enabled = user.account_enabled,
    i.usage_location = user.usage_location,
    i.deletion_timestamp = user.deletion_timestamp,
    i.create_date = user.create_date,
    i.company_name = user.company_name,
    i.mobile = user.mobile,
    i.office_location = user.office_location,
    i.preferred_language = user.preferred_language,
    i.department = user.department,
    i.region = $region
    WITH i
    MATCH (owner:AzureTenant{id: $tenant_id})
    MERGE (owner)-[r:RESOURCE]->(i)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    """

    tx.run(
        ingest_user,
        region="global",
        tenant_users_list=tenant_users_list,
        tenant_id=tenant_id,
        update_tag=update_tag,
    )


def cleanup_tenant_users(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('azure_import_tenant_users_cleanup.json', neo4j_session, common_job_parameters)


async def sync_tenant_users(
    neo4j_session: neo4j.Session, credentials: Credentials, tenant_id: str, update_tag: int,
    common_job_parameters: Dict,
) -> None:
    """
    Sync users from Microsoft Graph API to Neo4j.
    """
    client = get_graph_client(credentials.default_graph_credentials)
    tenant_users_list = await list_tenant_users(client, tenant_id)

    load_tenant_users(neo4j_session, tenant_id, tenant_users_list, update_tag)
    cleanup_tenant_users(neo4j_session, common_job_parameters)


@timeit
async def get_tenant_groups_list(client: GraphServiceClient, tenant_id: str, filter_query: Optional[str] = None) -> List[Dict]:
    """
    Get groups from Microsoft Graph API.
    Microsoft Graph API documentation: https://learn.microsoft.com/en-us/graph/api/group-list
    """
    try:
        request_config = None
        if filter_query:
            # Use a request configuration to add the $filter query parameter
            query_params = GroupsRequestBuilder.GroupsRequestBuilderGetQueryParameters(
                filter=filter_query,
            )
            request_config = GroupsRequestBuilder.GroupsRequestBuilderGetRequestConfiguration(
                query_parameters=query_params,
            )
        groups: List[Dict] = []
        response = await client.groups.get(request_configuration=request_config)
        if not response or not response.value:
            return []
        groups.extend(response.value)

        while response.odata_next_link:
            response = await client.groups.with_url(response.odata_next_link).get()
            groups.extend(response.value)
        tenant_groups_list = []

        for group in groups:
            # Convert the Graph API response to a dictionary
            group_id = getattr(group, 'id', None)
            if hasattr(group, 'as_dict'):
                group_dict = group.as_dict()
            else:
                group_dict = {
                    'id': group_id,
                    'display_name': getattr(group, 'display_name', None),
                    'mail': getattr(group, 'mail', None),
                    'mail_nickname': getattr(group, 'mail_nickname', None),
                    'mail_enabled': getattr(group, 'mail_enabled', None),
                    'security_enabled': getattr(group, 'security_enabled', None),
                    'visibility': getattr(group, 'visibility', None),
                    'classification': getattr(group, 'classification', None),
                    'created_date_time': getattr(group, 'created_date_time', datetime.utcnow()).isoformat(),
                    'description': getattr(group, 'description', None),
                    'on_premises_sync_enabled': getattr(group, 'on_premises_sync_enabled', None),
                    'on_premises_domain_name': getattr(group, 'on_premises_domain_name', None),
                    'on_premises_sam_account_name': getattr(group, 'on_premises_sam_account_name', None),
                    'on_premises_security_identifier': getattr(group, 'on_premises_security_identifier', None),
                    'renewed_date_time': getattr(group, 'renewed_date_time', datetime.utcnow()).isoformat(),
                    'security_identifier': getattr(group, 'security_identifier', None),
                }

            # Add tenant-specific ID for consistency with previous implementation
            group_dict['object_id'] = group_id
            group_dict['id'] = f"tenants/{tenant_id}/Groups/{group_id}"
            group_dict['consolelink'] = azure_console_link.get_console_link(
                iam_entity_type='group',
                id=group_id,
            )

            tenant_groups_list.append(group_dict)

        return tenant_groups_list

    except HttpResponseError as e:
        logger.warning(f"Error while retrieving tenant groups - {e}")
        return []


def _load_tenant_groups_tx(
    tx: neo4j.Transaction, tenant_id: str, tenant_groups_list: List[Dict], update_tag: int,
) -> None:
    ingest_group = """
    UNWIND $tenant_groups_list AS group
    MERGE (i:AzureGroup{id: group.id})
    ON CREATE SET i:AzurePrincipal,
    i.firstseen = timestamp(),
    i.region = $region,
    i.name = group.display_name
    SET i.lastupdated = $update_tag,
    i.mail = group.mail,
    i.object_id = group.object_id,
    i.visibility = group.visibility,
    i.classification = group.classification,
    i.created_date_time = group.created_date_time,
    i.security_enabled = group.security_enabled,
    i.mail_enabled = group.mail_enabled,
    i.mail_nickname = group.mail_nickname,
    i.description = group.description,
    i.group_types = group.group_types,
    i.on_premises_sync_enabled = group.on_premises_sync_enabled,
    i.on_premises_domain_name = group.on_premises_domain_name,
    i.on_premises_sam_account_name = group.on_premises_sam_account_name,
    i.on_premises_security_identifier = group.on_premises_security_identifier,
    i.renewed_date_time = group.renewed_date_time,
    i.security_identifier = group.security_identifier,
    i.region = $region
    WITH i
    MATCH (owner:AzureTenant{id: $tenant_id})
    MERGE (owner)-[r:RESOURCE]->(i)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    """

    tx.run(
        ingest_group,
        region="global",
        tenant_groups_list=tenant_groups_list,
        tenant_id=tenant_id,
        update_tag=update_tag,
    )


async def get_group_members(credentials: Credentials, group_id: str) -> List[Dict[str, Any]]:
    client: GraphServiceClient = get_default_graph_client(credentials.default_graph_credentials)
    members_data = []
    try:
        members: List[Dict] = []
        response = await client.groups.by_group_id(group_id.split("/")[-1]).members.get()
        members.extend(response.value)

        while response.odata_next_link:
            response = await client.groups.by_group_id(group_id.split("/")[-1]).members.with_url(response.odata_next_link).get()
            members.extend(response.value)

        if members:
            for member in members:
                if member.odata_type == "#microsoft.graph.group":
                    inherited_members: List[Dict] = []
                    response = await client.groups.by_group_id(member.id).members.get()
                    inherited_members.extend(response.value)

                    while response.odata_next_link:
                        response = await client.groups.by_group_id(member.id).members.with_url(response.odata_next_link).get()
                        inherited_members.extend(response.value)
                    for inherited_member in inherited_members:
                        members_data.append({
                            "id": inherited_member.id,
                            "display_name": inherited_member.display_name,
                            "mail": inherited_member.mail,
                            "group_id": group_id,
                        })
                members_data.append({
                    "id": member.id,
                    "display_name": member.display_name,
                    "mail": member.mail,
                    "group_id": group_id,
                })
    except Exception as e:
        logger.warning(f"error to get members of group {group_id} - {e}")
    return members_data


@timeit
def load_group_memberships(neo4j_session: neo4j.Session, memberships: List[Dict], update_tag: int) -> None:
    neo4j_session.write_transaction(_load_group_memberships_tx, memberships, update_tag)


@timeit
def _load_group_memberships_tx(tx: neo4j.Transaction, memberships: List[Dict], update_tag: int) -> None:
    ingest_memberships = """
    UNWIND $memberships AS membership
        MATCH (p:AzureGroup{id: membership.group_id})
        MATCH (pr:AzurePrincipal{object_id: membership.id})
        WITH p,pr
        MERGE (pr)-[r:MEMBER_AZURE_GROUP]->(p)
        ON CREATE SET
                r.firstseen = timestamp()
        SET
                r.lastupdated = $update_tag
    """

    tx.run(
        ingest_memberships,
        memberships=memberships,
        update_tag=update_tag,
    )


def cleanup_tenant_groups(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('azure_import_tenant_groups_cleanup.json', neo4j_session, common_job_parameters)


async def sync_tenant_groups(
    neo4j_session: neo4j.Session, credentials: Credentials, tenant_id: str, update_tag: int,
    common_job_parameters: Dict,
) -> None:
    """
    Sync groups from Microsoft Graph API to Neo4j.
    """
    client = get_graph_client(credentials.default_graph_credentials)
    tenant_groups_list = await get_tenant_groups_list(client, tenant_id)

    load_tenant_groups(neo4j_session, tenant_id, tenant_groups_list, update_tag)
    for group in tenant_groups_list:
        memberships = await get_group_members(credentials, group["id"])
        load_group_memberships(neo4j_session, memberships, update_tag)

    cleanup_tenant_groups(neo4j_session, common_job_parameters)


@timeit
async def get_tenant_applications_list(client: GraphServiceClient, tenant_id: str) -> List[Dict]:
    """
    Get applications from Microsoft Graph API.
    Microsoft Graph API documentation: https://learn.microsoft.com/en-us/graph/api/application-list
    """
    try:
        apps: List[Dict] = []
        response = await client.applications.get()
        if not response or not response.value:
            return []
        apps.extend(response.value)

        while response.odata_next_link:
            response = await client.applications.with_url(response.odata_next_link).get()
            apps.extend(response.value)

        tenant_applications_list = []

        for app in apps:
            # Convert the Graph API response to a dictionary
            if hasattr(app, 'as_dict'):
                app_dict = app.as_dict()
            else:
                app_dict = {
                    'id': getattr(app, 'id', None),
                    'display_name': getattr(app, 'display_name', None),
                    'app_id': getattr(app, 'app_id', None),
                    'created_date_time': getattr(app, 'created_date_time', datetime.utcnow()).isoformat(),
                    'description': getattr(app, 'description', None),
                    'deleted_date_time': getattr(app, 'deleted_date_time', None) if getattr(app, 'deleted_date_time', None) else datetime.utcnow().isoformat(),
                    'publisher_domain': getattr(app, 'publisher_domain', None),
                    'sign_in_audience': getattr(app, 'sign_in_audience', None),
                    'application_template_id': getattr(app, 'application_template_id', None),
                    'disabled_by_microsoft_status': getattr(app, 'disabled_by_microsoft_status', None),
                    'is_device_only_auth_supported': getattr(app, 'is_device_only_auth_supported', None),
                    'is_fallback_public_client': getattr(app, 'is_fallback_public_client', None),
                }

            # Add tenant-specific ID for consistency with previous implementation
            app_dict['object_id'] = app_dict.get('id')
            app_dict['id'] = f"tenants/{tenant_id}/Applications/{app_dict.get('id')}"
            app_dict['consolelink'] = azure_console_link.get_console_link(
                iam_entity_type='application',
                id=app_dict.get('app_id'),
            )

            tenant_applications_list.append(app_dict)

        return tenant_applications_list

    except HttpResponseError as e:
        logger.warning(f"Error while retrieving tenant applications - {e}")
        return []


def _load_tenant_applications_tx(
    tx: neo4j.Transaction, tenant_id: str, tenant_applications_list: List[Dict], update_tag: int,
) -> None:
    ingest_app = """
    UNWIND $tenant_applications_list AS app
    MERGE (i:AzureApplication{id: app.id})
    ON CREATE SET i:AzurePrincipal,
    i.firstseen = timestamp(),
    i.object_id = app.object_id,
    i.region = $region,
    i.consolelink = app.consolelink,
    i.app_id = app.app_id
    SET i.lastupdated = $update_tag,
    i.name = app.display_name,
    i.publisher_domain = app.publisher_domain,
    i.sign_in_audience = app.sign_in_audience,
    i.created_date_time = app.created_date_time,
    i.description = app.description,
    i.deleted_date_time = app.deleted_date_time,
    i.application_template_id = app.application_template_id,
    i.disabled_by_microsoft_status = app.disabled_by_microsoft_status,
    i.is_device_only_auth_supported = app.is_device_only_auth_supported,
    i.is_fallback_public_client = app.is_fallback_public_client,
    i.region = $region
    WITH i
    MATCH (owner:AzureTenant{id: $tenant_id})
    MERGE (owner)-[r:RESOURCE]->(i)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    """

    tx.run(
        ingest_app,
        region="global",
        tenant_applications_list=tenant_applications_list,
        tenant_id=tenant_id,
        update_tag=update_tag,
    )


def cleanup_tenant_applications(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('azure_import_tenant_applications_cleanup.json', neo4j_session, common_job_parameters)


async def sync_tenant_applications(
    neo4j_session: neo4j.Session, credentials: Credentials, tenant_id: str, update_tag: int,
    common_job_parameters: Dict,
) -> None:
    """
    Sync applications from Microsoft Graph API to Neo4j.
    """
    client = get_graph_client(credentials.default_graph_credentials)
    tenant_applications_list = await get_tenant_applications_list(client, tenant_id)

    load_tenant_applications(neo4j_session, tenant_id, tenant_applications_list, update_tag)
    cleanup_tenant_applications(neo4j_session, common_job_parameters)


@timeit
async def get_tenant_service_accounts_list(client: GraphServiceClient, tenant_id: str) -> List[Dict]:
    """
    Get service principals from Microsoft Graph API.
    Microsoft Graph API documentation: https://learn.microsoft.com/en-us/graph/api/serviceprincipal-list
    """
    try:
        service_accounts: List[Dict] = []
        response = await client.service_principals.get()
        if not response or not response.value:
            return []
        service_accounts.extend(response.value)

        while response.odata_next_link:
            response = await client.service_principals.with_url(response.odata_next_link).get()
            service_accounts.extend(response.value)

        tenant_service_accounts_list = []

        for sp in service_accounts:
            # Convert the Graph API response to a dictionary
            if hasattr(sp, 'as_dict'):
                sp_dict = sp.as_dict()
            else:
                sp_dict = {
                    'id': getattr(sp, 'id', None),
                    'display_name': getattr(sp, 'display_name', None),
                    'app_id': getattr(sp, 'app_id', None),
                    'client_id': getattr(sp, 'app_id', None),
                    'account_enabled': getattr(sp, 'account_enabled', None),
                    'app_display_name': getattr(sp, 'app_display_name', None),
                    'app_role_assignment_required': getattr(sp, 'app_role_assignment_required', None),
                    'application_template_id': getattr(sp, 'application_template_id', None),
                    'created_date_time': getattr(sp, 'createdDateTime', None),
                    'deleted_date_time': getattr(sp, 'deleted_date_time', None),
                    'description': getattr(sp, 'description', None),
                    'disabled_by_microsoft_status': getattr(sp, 'disabled_by_microsoft_status', None),
                    'homepage': getattr(sp, 'homepage', None),
                    'login_url': getattr(sp, 'login_url', None),
                    'logout_url': getattr(sp, 'logout_url', None),
                    'preferred_single_sign_on_mode': getattr(sp, 'preferred_single_sign_on_mode', None),
                    'preferred_token_signing_key_thumbprint': getattr(sp, 'preferred_token_signing_key_thumbprint', None),
                    'service_principal_type': getattr(sp, 'service_principal_type', None),
                    'sign_in_audience': getattr(sp, 'sign_on_audience', None),
                    'token_encryption_key_id': getattr(sp, 'token_encryption_key_id', None),
                }

            # Add tenant-specific ID for consistency with previous implementation
            sp_dict['object_id'] = sp_dict.get('id')
            sp_dict['id'] = f"tenants/{tenant_id}/ServiceAccounts/{sp_dict.get('id')}"
            sp_dict['consolelink'] = azure_console_link.get_console_link(
                id=sp_dict.get('id'),
                app_id=sp_dict.get('app_id'),
                iam_entity_type='service_principal',
            )

            tenant_service_accounts_list.append(sp_dict)

        return tenant_service_accounts_list

    except HttpResponseError as e:
        logger.warning(f"Error while retrieving tenant service accounts - {e}")
        return []


def _load_tenant_service_accounts_tx(
    tx: neo4j.Transaction, tenant_id: str, tenant_service_accounts_list: List[Dict], update_tag: int,
) -> None:
    ingest_app = """
    UNWIND $tenant_service_accounts_list AS service
    MERGE (i:AzureServiceAccount{id: service.id})
    ON CREATE SET i:AzurePrincipal,
    i.firstseen = timestamp(),
    i.consolelink = service.consolelink,
    i.region = $region,
    i.object_id = service.object_id
    SET i.lastupdated = $update_tag,
    i.name = service.display_name,
    i.account_enabled = service.account_enabled,
    i.app_id = service.app_id,
    i.client_id = service.client_id,
    i.app_display_name = service.app_display_name,
    i.app_owner_organization_id = service.app_owner_organization_id,
    i.app_role_assignment_required = service.app_role_assignment_required,
    i.application_template_id = service.application_template_id,
    i.created_date_time = service.created_date_time,
    i.deleted_date_time = service.deleted_date_time,
    i.description = service.description,
    i.disabled_by_microsoft_status = service.disabled_by_microsoft_status,
    i.homepage = service.homepage,
    i.login_url = service.login_url,
    i.logout_url = service.logout_url,
    i.preferred_single_sign_on_mode = service.preferred_single_sign_on_mode,
    i.preferred_token_signing_key_thumbprint = service.preferred_token_signing_key_thumbprint,
    i.service_principal_type = service.service_principal_type,
    i.sign_in_audience = service.sign_in_audience,
    i.token_encryption_key_id = service.token_encryption_key_id,
    i.region = $region
    WITH i
    MATCH (owner:AzureTenant{id: $tenant_id})
    MERGE (owner)-[r:RESOURCE]->(i)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    """

    tx.run(
        ingest_app,
        region="global",
        tenant_service_accounts_list=tenant_service_accounts_list,
        tenant_id=tenant_id,
        update_tag=update_tag,
    )


def cleanup_tenant_service_accounts(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('azure_import_tenant_service_accounts_cleanup.json', neo4j_session, common_job_parameters)


async def sync_tenant_service_accounts(
    neo4j_session: neo4j.Session, credentials: Credentials, tenant_id: str, update_tag: int,
    common_job_parameters: Dict,
) -> None:
    """
    Sync service principals from Microsoft Graph API to Neo4j.
    """
    client = get_graph_client(credentials.default_graph_credentials)
    tenant_service_accounts_list = await get_tenant_service_accounts_list(client, tenant_id)

    load_tenant_service_accounts(neo4j_session, tenant_id, tenant_service_accounts_list, update_tag)
    cleanup_tenant_service_accounts(neo4j_session, common_job_parameters)


@timeit
async def get_tenant_domains_list(client: GraphServiceClient, tenant_id: str) -> List[Dict]:
    """
    Get domains from Microsoft Graph API.
    Microsoft Graph API documentation: https://learn.microsoft.com/en-us/graph/api/domain-list

    Note: Microsoft Graph's domain resource is accessed through the domains endpoint,
    unlike Azure AD Graph which had a separate domains.list() method.
    """
    try:
        # Access domains through the Microsoft Graph API
        response = await client.domains.get()
        if not response or not response.value:
            return []

        tenant_domains_list = []

        for domain in response.value:
            if hasattr(domain, 'as_dict'):
                domain_dict = domain.as_dict()
            else:
                domain_dict = {
                    'id': getattr(domain, 'id', None),
                    'authentication_type': getattr(domain, 'authentication_type', None),
                    'availability_status': getattr(domain, 'availability_status', None),
                    'is_admin_managed': getattr(domain, 'is_admin_managed', None),
                    'is_default': getattr(domain, 'is_default', None),
                    'is_initial': getattr(domain, 'is_initial', None),
                    'is_root': getattr(domain, 'is_root', None),
                    'is_verified': getattr(domain, 'is_verified', None),
                    'password_notification_window_in_days': getattr(domain, 'password_notification_window_in_days', None),
                    'password_validity_period_in_days': getattr(domain, 'password_validity_period_in_days', None),
                    'supported_services': getattr(domain, 'supported_services', []),
                }

                # Handle state property which is a complex object
                if hasattr(domain, 'state') and domain.state:
                    domain_dict['state'] = {
                        'last_action_date_time': getattr(domain.state, 'last_action_date_time', None),
                        'operation': getattr(domain.state, 'operation', None),
                        'status': getattr(domain.state, 'status', None),
                    }

            # Add custom properties
            domain_dict['id'] = f"tenants/{tenant_id}/domains/{domain_dict.get('id')}"
            domain_dict['consolelink'] = azure_console_link.get_console_link(
                id=domain_dict.get('id'),
                iam_entity_type='domain',
            )

            tenant_domains_list.append(domain_dict)

        return tenant_domains_list

    except HttpResponseError as e:
        logger.warning(f"Error while retrieving tenant domains - {e}")
        return []


def _load_tenant_domains_tx(
    tx: neo4j.Transaction, tenant_id: str, tenant_domains_list: List[Dict], update_tag: int,
) -> None:
    ingest_domain = """
    UNWIND $tenant_domains_list AS domain
    MERGE (i:AzureDomain{id: domain.id})
    ON CREATE SET i:AzurePrincipal,
    i.firstseen = timestamp(),
    i.consolelink = domain.consolelink,
    i.region = $region,
    i.create_date = $createDate
    SET i.lastupdated = $update_tag,
    i.authentication_type = domain.authentication_type,
    i.availability_status = domain.availability_status,
    i.is_admin_managed = domain.is_admin_managed,
    i.is_default = domain.is_default,
    i.is_initial = domain.is_initial,
    i.is_root = domain.is_root,
    i.is_verified = domain.is_verified,
    i.password_notification_window_in_days = domain.password_notification_window_in_days,
    i.password_validity_period_in_days = domain.password_validity_period_in_days,
    i.supported_services = domain.supported_services,
    i.state_last_action_date_time = CASE WHEN domain.state IS NOT NULL THEN domain.state.last_action_date_time ELSE null END,
    i.state_operation = CASE WHEN domain.state IS NOT NULL THEN domain.state.operation ELSE null END,
    i.state_status = CASE WHEN domain.state IS NOT NULL THEN domain.state.status ELSE null END,
    i.region = $region
    WITH i
    MATCH (owner:AzureTenant{id: $tenant_id})
    MERGE (owner)-[r:RESOURCE]->(i)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    """

    tx.run(
        ingest_domain,
        region="global",
        tenant_domains_list=tenant_domains_list,
        tenant_id=tenant_id,
        createDate=datetime.utcnow(),
        update_tag=update_tag,
    )


def cleanup_tenant_domains(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('azure_import_tenant_domains_cleanup.json', neo4j_session, common_job_parameters)


async def sync_tenant_domains(
    neo4j_session: neo4j.Session, credentials: Credentials, tenant_id: str, update_tag: int,
    common_job_parameters: Dict,
) -> None:
    """
    Sync domains from Microsoft Graph API to Neo4j.
    """
    client = get_graph_client(credentials.default_graph_credentials)
    tenant_domains_list = await get_tenant_domains_list(client, tenant_id)

    load_tenant_domains(neo4j_session, tenant_id, tenant_domains_list, update_tag)
    cleanup_tenant_domains(neo4j_session, common_job_parameters)


@timeit
def get_roles_list(subscription_id: str, client: AuthorizationManagementClient, common_job_parameters: Dict) -> List[Dict]:
    try:
        role_definitions_list = list(
            map(lambda x: x.as_dict(), client.role_definitions.list(scope=f"/subscriptions/{subscription_id}")),
        )
        for role in role_definitions_list:
            if role.get('type') == 'Microsoft.Authorization/roleDefinitions' or role.get('role_type') == 'BuiltInRole':
                role["role_owner_type"] = 'predefined'

            else:
                role["role_owner_type"] = 'custom'

            role["identity_id"] = role['id'].split("/")[-1]
            role['consolelink'] = azure_console_link.get_console_link(
                id=role['id'], primary_ad_domain_name=common_job_parameters['Azure_Primary_AD_Domain_Name'],
            )
            permissions = []
            for permission in role.get('permissions', []):
                for action in permission.get('actions', []):
                    permissions.append(action)
                for data_action in permission.get('dataActions', []):
                    permissions.append(data_action)
            role['permissions'] = list(set(permissions))

        return role_definitions_list

    except HttpResponseError as e:
        logger.warning(f"Error while retrieving roles - {e}")
        return []


@timeit
def get_role_assignments(client: AuthorizationManagementClient, common_job_parameters: Dict) -> List[Dict]:
    try:
        role_assignments_list = list(
            map(lambda x: x.as_dict(), client.role_assignments.list()),
        )

        return role_assignments_list

    except HttpResponseError as e:
        logger.warning(f"Error while retrieving roles - {e}")
        return []


@timeit
def get_managed_identity_list(client: ManagedServiceIdentityClient, subscription_id: str, common_job_parameters: Dict) -> List[Dict]:
    try:
        managed_identity_list = list(
            map(lambda x: x.as_dict(), client.user_assigned_identities.list_by_subscription()),
        )

        for managed_identity in managed_identity_list:
            managed_identity['consolelink'] = azure_console_link.get_console_link(
                id=managed_identity['id'], primary_ad_domain_name=common_job_parameters['Azure_Primary_AD_Domain_Name'],
            )
            managed_identity['location'] = managed_identity.get('location', '').replace(" ", "").lower()
        return managed_identity_list
    except HttpResponseError as e:
        logger.warning(f"Error while retrieving managed identity - {e}")
        return []


def _load_roles_tx(
    tx: neo4j.Transaction, tenant_id: str, roles_list: List[Dict], role_assignments_list: List[Dict], update_tag: int, SUBSCRIPTION_ID: str,
) -> None:
    ingest_role = """
    UNWIND $roles_list AS role
    MERGE (i:AzureRole{id: role.id})
    ON CREATE SET i.firstseen = timestamp(),
    i.name = role.role_name,
    i.consolelink = role.consolelink,
    i.region = $region,
    i.create_date = $createDate
    SET i.lastupdated = $update_tag,
    i.roleName = role.role_name,
    i.permissions = role.permissions,
    i.type = role.type,
    i.role_type = role.role_type,
    i.identity_id = role.identity_id,
    i.role_owner_type = role.role_owner_type,
    i.region = $region
    WITH i,role
    MATCH (t:AzureTenant{id: $tenant_id})
    MERGE (t)-[tr:RESOURCE]->(i)
    ON CREATE SET tr.firstseen = timestamp()
    SET tr.lastupdated = $update_tag
    WITH i,role
    MATCH (sub:AzureSubscription{id: $SUBSCRIPTION_ID})
    MERGE (sub)<-[sr:HAS_ACCESS]-(i)
    ON CREATE SET sr.firstseen = timestamp()
    SET sr.lastupdated = $update_tag
    """

    tx.run(
        ingest_role,
        region="global",
        roles_list=roles_list,
        update_tag=update_tag,
        createDate=datetime.utcnow(),
        tenant_id=tenant_id,
        SUBSCRIPTION_ID=SUBSCRIPTION_ID,
    )

    attach_role = """
    MATCH (principal:AzurePrincipal{object_id: $principal_id})
    WITH principal
    MATCH (i:AzureRole{id: $role})
    WITH i,principal
    MERGE (principal)-[r:ASSUME_ROLE]->(i)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    """
    for role_assignment in role_assignments_list:
        tx.run(
            attach_role,
            role=role_assignment.get('role_definition_id', role_assignment.get('properties', {}).get('role_definition_id')),
            principal_id=role_assignment.get('principal_id', role_assignment.get('properties', {}).get('principal_id')),
            update_tag=update_tag,
        )


def _load_managed_identities_tx(
    tx: neo4j.Transaction, tenant_id: str, managed_identity_list: List[Dict], update_tag: int,
) -> None:
    ingest_managed_identity = """
    UNWIND $managed_identity_list AS managed_identity
    MERGE (i:AzureManagedIdentity{id: toLower(managed_identity.id)})
    ON CREATE SET i:AzurePrincipal,
    i.firstseen = timestamp(),
    i.location = managed_identity.location,
    i.region = managed_identity.location
    SET i.lastupdated = $update_tag,
    i.name = managed_identity.name,
    i.consolelink = managed_identity.consolelink,
    i.location = managed_identity.location,
    i.region = managed_identity.location,
    i.type = managed_identity.type,
    i.object_id = managed_identity.principal_id,
    i.principal_id = managed_identity.principal_id,
    i.client_id = managed_identity.client_id
    WITH i
    MATCH (t:AzureTenant{id: $tenant_id})
    MERGE (t)-[tr:RESOURCE]->(i)
    ON CREATE SET tr.firstseen = timestamp()
    SET tr.lastupdated = $update_tag
    """

    tx.run(
        ingest_managed_identity,
        managed_identity_list=managed_identity_list,
        update_tag=update_tag,
        tenant_id=tenant_id,
    )


def cleanup_roles(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('azure_import_tenant_roles_cleanup.json', neo4j_session, common_job_parameters)


def cleanup_managed_identities(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('azure_import_managed_identity_cleanup.json', neo4j_session, common_job_parameters)


def sync_roles(
    neo4j_session: neo4j.Session, credentials: Credentials, tenant_id: str, update_tag: int,
    common_job_parameters: Dict, ingested_principal_ids: Optional[set] = None,
) -> None:
    client = get_authorization_client(credentials.arm_credentials, credentials.subscription_id)
    roles_list = get_roles_list(credentials.subscription_id, client, common_job_parameters)
    role_assignments_list = get_role_assignments(client, common_job_parameters)
    if ingested_principal_ids is not None:
        role_assignments_list = [
            assignment for assignment in role_assignments_list
            if assignment.get('principal_id') in ingested_principal_ids
        ]
    load_roles(neo4j_session, tenant_id, roles_list, role_assignments_list, update_tag, credentials.subscription_id)
    cleanup_roles(neo4j_session, common_job_parameters)


def sync_managed_identity(
    neo4j_session: neo4j.Session, credentials: Credentials, tenant_id: str, update_tag: int,
    common_job_parameters: Dict,
) -> None:
    client = get_managed_identity_client(credentials.arm_credentials, credentials.subscription_id)
    managed_identity_list = get_managed_identity_list(client, credentials.subscription_id, common_job_parameters)
    load_managed_identities(neo4j_session, tenant_id, managed_identity_list, update_tag)
    cleanup_managed_identities(neo4j_session, common_job_parameters)


def _set_used_state_tx(
    tx: neo4j.Transaction, tenant_id: str, common_job_parameters: Dict, update_tag: int,
) -> None:
    ingest_role_used = """
    MATCH (:CloudanixWorkspace{id: $WORKSPACE_ID})-[:OWNER]->
    (:AzureTenant{id: $AZURE_TENANT_ID})-[r:RESOURCE]->(n:AzureRole)<-[:ASSUME_ROLE]-(p:AzurePrincipal)
    WHERE n.lastupdated = $update_tag
    SET n.isUsed = $isUsed,
    p.isUsed = $isUsed
    """

    tx.run(
        ingest_role_used,
        WORKSPACE_ID=common_job_parameters['WORKSPACE_ID'],
        update_tag=update_tag,
        AZURE_TENANT_ID=tenant_id,
        isUsed=True,
    )

    ingest_entity_unused = """
    MATCH (:CloudanixWorkspace{id: $WORKSPACE_ID})-[:OWNER]->
    (:AzureTenant{id: $AZURE_TENANT_ID})-[r:RESOURCE]->(n)
    WHERE NOT EXISTS(n.isUsed) AND n.lastupdated = $update_tag
    AND labels(n) IN [['AzureUser'], ['AzureGroup'], ['AzureServiceAccount'], ['AzureRole']]
    SET n.isUsed = $isUsed
    """

    tx.run(
        ingest_entity_unused,
        WORKSPACE_ID=common_job_parameters['WORKSPACE_ID'],
        update_tag=update_tag,
        AZURE_TENANT_ID=tenant_id,
        isUsed=False,
    )


async def sync_scoped_users_and_groups(
    neo4j_session: neo4j.Session, credentials: Credentials, tenant_id: str, update_tag: int,
    common_job_parameters: Dict, scoped_group_ids: List[str],
) -> Set[str]:
    """
    Syncs only specified groups and their members (users).
    """
    client = get_graph_client(credentials.default_graph_credentials)

    # 1. Fetch only the scoped groups in batches to avoid URL length limits.
    scoped_groups = []
    group_id_list = list(scoped_group_ids)
    for i in range(0, len(group_id_list), SAFE_BATCH_SIZE):
        batch_ids = group_id_list[i:i + SAFE_BATCH_SIZE]
        id_filter_str = "id in ({})".format(','.join(f"'{id_val['id']}'" for id_val in batch_ids))
        group_batch = await get_tenant_groups_list(client, tenant_id, filter_query=id_filter_str)
        if group_batch:
            scoped_groups.extend(group_batch)

    if not scoped_groups:
        return set()

    # 2. Fetch members for each scoped group
    all_memberships = []
    all_member_ids = set()
    for group in scoped_groups:
        memberships = await get_group_members(credentials, group["id"])
        if memberships:
            all_memberships.extend(memberships)
            for member in memberships:
                all_member_ids.add(member['id'])

    # 3. Fetch only the required users in batches using a $filter query to avoid URL length limits.
    scoped_users = []
    if all_member_ids:
        member_id_list = list(all_member_ids)
        user_fetch_tasks = []
        for i in range(0, len(member_id_list), SAFE_BATCH_SIZE):
            batch_ids = member_id_list[i:i + SAFE_BATCH_SIZE]
            id_filter_str = "id in ({})".format(','.join(f"'{id_val}'" for id_val in batch_ids))
            user_fetch_tasks.append(list_tenant_users(client, tenant_id, filter_query=id_filter_str))

        # Run all batch fetches concurrently
        user_batch_responses = await asyncio.gather(*user_fetch_tasks)
        for user_batch in user_batch_responses:
            if user_batch:
                scoped_users.extend(user_batch)

    # 4. Load the filtered data into Neo4j
    load_tenant_groups(neo4j_session, tenant_id, scoped_groups, update_tag)
    if scoped_users:
        load_tenant_users(neo4j_session, tenant_id, scoped_users, update_tag)

    if all_memberships:
        load_group_memberships(neo4j_session, all_memberships, update_tag)

    # 5. Collect and return the IDs of all ingested principals
    ingested_principal_ids = {u.get('object_id') for u in scoped_users}
    ingested_principal_ids.update({g.get('object_id') for g in scoped_groups})

    # 6. Run cleanup jobs
    cleanup_tenant_users(neo4j_session, common_job_parameters)
    cleanup_tenant_groups(neo4j_session, common_job_parameters)

    return ingested_principal_ids


@timeit
async def async_sync(
    neo4j_session: neo4j.Session, credentials: Credentials, tenant_id: str, update_tag: int,
    common_job_parameters: Dict,
) -> None:
    scoped_group_ids = common_job_parameters.get('GROUPS', [])
    ingested_principal_ids: Optional[set] = None
    try:
        if common_job_parameters.get("DEFAULT_SUBSCRIPTION") == credentials.subscription_id or not common_job_parameters.get("DEFAULT_SUBSCRIPTION"):
            if scoped_group_ids:
                # Only sync specified groups and their users
                ingested_principal_ids = await sync_scoped_users_and_groups(
                    neo4j_session, credentials, tenant_id,
                    update_tag, common_job_parameters, scoped_group_ids,
                )
            else:
                # Sync all users and groups
                await sync_tenant_users(
                    neo4j_session, credentials, tenant_id,
                    update_tag, common_job_parameters,
                )
                await sync_tenant_groups(
                    neo4j_session, credentials, tenant_id,
                    update_tag, common_job_parameters,
                )

            await sync_tenant_applications(
                neo4j_session, credentials,
                tenant_id, update_tag, common_job_parameters,
            )
            await sync_tenant_service_accounts(
                neo4j_session, credentials,
                tenant_id, update_tag, common_job_parameters,
            )
            await sync_tenant_domains(neo4j_session, credentials, tenant_id, update_tag, common_job_parameters)
            sync_managed_identity(
                neo4j_session, credentials, tenant_id, update_tag, common_job_parameters,
            )

        sync_roles(
            neo4j_session, credentials, tenant_id, update_tag, common_job_parameters, ingested_principal_ids,
        )
        set_used_state(neo4j_session, tenant_id, common_job_parameters, update_tag)

    except Exception as ex:
        logger.error(f'exception from IAM - {ex}', exc_info=True, stack_info=True)


@timeit
def sync(
    neo4j_session: neo4j.Session, credentials: Credentials, tenant_id: str, update_tag: int,
    common_job_parameters: Dict,
) -> None:
    """
    Sync IAM resources from Microsoft Graph API to Neo4j.
    """
    logger.info("Syncing IAM for Tenant '%s'.", tenant_id)

    common_job_parameters['AZURE_TENANT_ID'] = tenant_id
    asyncio.run(async_sync(neo4j_session, credentials, tenant_id, update_tag, common_job_parameters))
