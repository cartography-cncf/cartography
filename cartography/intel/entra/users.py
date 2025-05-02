import logging
from typing import Any

import neo4j
from azure.identity import ClientSecretCredential
from msgraph import GraphServiceClient
from msgraph.generated.models.organization import Organization
from msgraph.generated.models.user import User

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.entra.tenant import EntraTenantSchema
from cartography.models.entra.user import EntraUserSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
async def get_tenant(client: GraphServiceClient) -> Organization:
    """
    Get tenant information from Microsoft Graph API
    """
    org = await client.organization.get()
    return org.value[0]  # Get the first (and typically only) tenant


@timeit
async def get_users(client: GraphServiceClient) -> list[User]:
    """
    Get all users from Microsoft Graph API with pagination support
    """
    all_users: list[User] = []
    request_configuration = client.users.UsersRequestBuilderGetRequestConfiguration(
        query_parameters=client.users.UsersRequestBuilderGetQueryParameters(
            # Request more items per page to reduce number of API calls
            top=999,
        ),
    )

    page = await client.users.get(request_configuration=request_configuration)
    while page:
        all_users.extend(page.value)
        if not page.odata_next_link:
            break
        page = await client.users.with_url(page.odata_next_link).get()

    return all_users


@timeit
def transform_users(users: list[User]) -> list[dict[str, Any]]:
    """
    Transform the API response into the format expected by our schema
    """
    result: list[dict[str, Any]] = []
    for user in users:
        transformed_user = {
            "id": user.id,
            "user_principal_name": user.user_principal_name,
            "display_name": user.display_name,
            "given_name": user.given_name,
            "surname": user.surname,
            "mail": user.mail,
            "other_mails": user.other_mails,
            "preferred_language": user.preferred_language,
            "preferred_name": user.preferred_name,
            "state": user.state,
            "usage_location": user.usage_location,
            "user_type": user.user_type,
            "show_in_address_list": user.show_in_address_list,
            "sign_in_sessions_valid_from_date_time": user.sign_in_sessions_valid_from_date_time,
            "security_identifier": user.on_premises_security_identifier,
            "account_enabled": user.account_enabled,
            "age_group": user.age_group,
            "business_phones": user.business_phones,
            "city": user.city,
            "company_name": user.company_name,
            "consent_provided_for_minor": user.consent_provided_for_minor,
            "country": user.country,
            "created_date_time": user.created_date_time,
            "creation_type": user.creation_type,
            "deleted_date_time": user.deleted_date_time,
            "department": user.department,
            "employee_id": user.employee_id,
            "employee_type": user.employee_type,
            "external_user_state": user.external_user_state,
            "external_user_state_change_date_time": user.external_user_state_change_date_time,
            "hire_date": user.hire_date,
            "is_management_restricted": user.is_management_restricted,
            "is_resource_account": user.is_resource_account,
            "job_title": user.job_title,
            "last_password_change_date_time": user.last_password_change_date_time,
            "mail_nickname": user.mail_nickname,
            "office_location": user.office_location,
            "on_premises_distinguished_name": user.on_premises_distinguished_name,
            "on_premises_domain_name": user.on_premises_domain_name,
            "on_premises_immutable_id": user.on_premises_immutable_id,
            "on_premises_last_sync_date_time": user.on_premises_last_sync_date_time,
            "on_premises_sam_account_name": user.on_premises_sam_account_name,
            "on_premises_security_identifier": user.on_premises_security_identifier,
            "on_premises_sync_enabled": user.on_premises_sync_enabled,
            "on_premises_user_principal_name": user.on_premises_user_principal_name,
        }
        result.append(transformed_user)
    return result


@timeit
def transform_tenant(tenant: Organization, tenant_id: str) -> dict[str, Any]:
    """
    Transform the tenant data into the format expected by our schema
    """
    return {
        "id": tenant_id,
        "created_date_time": tenant.created_date_time,
        "default_usage_location": tenant.default_usage_location,
        "deleted_date_time": tenant.deleted_date_time,
        "display_name": tenant.display_name,
        "marketing_notification_emails": tenant.marketing_notification_emails,
        "mobile_device_management_authority": tenant.mobile_device_management_authority,
        "on_premises_last_sync_date_time": tenant.on_premises_last_sync_date_time,
        "on_premises_sync_enabled": tenant.on_premises_sync_enabled,
        "partner_tenant_type": tenant.partner_tenant_type,
        "postal_code": tenant.postal_code,
        "preferred_language": tenant.preferred_language,
        "state": tenant.state,
        "street": tenant.street,
        "tenant_type": tenant.tenant_type,
    }


@timeit
def load_tenant(
    neo4j_session: neo4j.Session,
    tenant: dict[str, Any],
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        EntraTenantSchema(),
        [tenant],
        lastupdated=update_tag,
    )


@timeit
def load_users(
    neo4j_session: neo4j.Session,
    users: list[dict[str, Any]],
    tenant_id: str,
    update_tag: int,
) -> None:
    logger.info(f"Loading {len(users)} Entra users")
    load(
        neo4j_session,
        EntraUserSchema(),
        users,
        lastupdated=update_tag,
        TENANT_ID=tenant_id,
    )


def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(EntraUserSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
async def sync_entra_users(
    neo4j_session: neo4j.Session,
    tenant_id: str,
    client_id: str,
    client_secret: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Sync Entra users and tenant information
    :param neo4j_session: Neo4J session for database interface
    :param tenant_id: Entra tenant ID
    :param client_id: Entra application client ID
    :param client_secret: Entra application client secret
    :param update_tag: Timestamp used to determine data freshness
    :param common_job_parameters: dict of other job parameters to carry to sub-jobs
    :return: None
    """
    # Initialize Graph client
    credential = ClientSecretCredential(
        tenant_id=tenant_id,
        client_id=client_id,
        client_secret=client_secret,
    )
    client = GraphServiceClient(
        credential, scopes=["https://graph.microsoft.com/.default"]
    )

    # Get tenant information
    tenant = await get_tenant(client)
    users = await get_users(client)

    transformed_users = transform_users(users)
    transformed_tenant = transform_tenant(tenant, tenant_id)

    load_tenant(neo4j_session, transformed_tenant, update_tag)
    load_users(neo4j_session, transformed_users, tenant_id, update_tag)

    cleanup(neo4j_session, common_job_parameters)
