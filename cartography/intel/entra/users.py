import logging
from typing import Any
from typing import AsyncGenerator
from typing import Generator

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

# NOTE:
# Microsoft Graph imposes limits on the length of the $select clause as well as
# the number of properties that can be selected in a single request.  In
# practice we have seen 400 Bad Request responses that bubble up as
# `Microsoft.SharePoint.Client.InvalidClientQueryException` once that limit is
# breached (Graph internally rewrites the next-link using a SharePoint style
# `id in (…)` filter which is then rejected).
#
# To avoid tripping this bug we only request a *core* subset of user attributes
# that are most commonly used in downstream analysis.  The transform() function
# tolerates missing attributes (the generated MS Graph SDK simply returns
# `None` for properties that are not present in the payload), so fetching fewer
# fields is safe – we merely get more `null` values in the graph.
#
# If you need additional attributes in the future, append them here but keep the
# total character count of the comma-separated list comfortably below 500 and
# stay within the official v1.0 contract (beta-only fields cause similar
# failures). 20–25 fields is a good rule-of-thumb.
#
# References:
#   • https://learn.microsoft.com/graph/query-parameters#select-parameter
#   • https://learn.microsoft.com/graph/api/user-list?view=graph-rest-1.0
#
USER_SELECT_FIELDS = [
    "id",
    "userPrincipalName",
    "displayName",
    "givenName",
    "surname",
    "mail",
    "mobilePhone",
    "businessPhones",
    "jobTitle",
    "department",
    "officeLocation",
    "city",
    "country",
    "companyName",
    "preferredLanguage",
    "employeeId",
    "employeeType",
    "accountEnabled",
    "ageGroup",
]


@timeit
async def get_tenant(client: GraphServiceClient) -> Organization:
    """
    Get tenant information from Microsoft Graph API
    """
    org = await client.organization.get()
    return org.value[0]  # Get the first (and typically only) tenant


@timeit
async def get_users(client: GraphServiceClient) -> AsyncGenerator[User, None]:
    """Fetch all users with their manager reference in as few requests as possible.

    We leverage `$expand=manager($select=id)` so the manager's *id* is hydrated
    alongside every user record.  This avoids making a second round-trip per
    user – vastly reducing latency and eliminating the noisy 404s that occur
    when a user has no manager assigned.
    """

    request_configuration = client.users.UsersRequestBuilderGetRequestConfiguration(
        query_parameters=client.users.UsersRequestBuilderGetQueryParameters(
            top=999,
            select=USER_SELECT_FIELDS,
            expand=["manager($select=id)"],
        ),
    )

    page = await client.users.get(request_configuration=request_configuration)
    while page:
        if page.value:
            for user in page.value:
                yield user
        if not page.odata_next_link:
            break

        try:
            page = await client.users.with_url(page.odata_next_link).get()
        except Exception as e:
            logger.error(
                "Failed to fetch next page of Entra ID users – stopping pagination early: %s",
                e,
            )
            break


@timeit
# The manager reference is now embedded in the user objects courtesy of the
# `$expand` we added above, so we no longer need a separate `manager_map`.
def transform_users(users: list[User]) -> Generator[dict[str, Any], None, None]:
    """Convert MS Graph SDK `User` models into dicts matching our schema."""

    for user in users:
        manager_id: str | None = None
        if getattr(user, "manager", None) is not None:
            # The SDK materialises `manager` as a DirectoryObject (or subclass)
            manager_id = getattr(user.manager, "id", None)

        yield {
            "id": user.id,
            "user_principal_name": user.user_principal_name,
            "display_name": user.display_name,
            "given_name": user.given_name,
            "surname": user.surname,
            "mail": user.mail,
            "mobile_phone": user.mobile_phone,
            "business_phones": user.business_phones,
            "job_title": user.job_title,
            "department": user.department,
            "office_location": user.office_location,
            "city": user.city,
            "state": user.state,
            "country": user.country,
            "company_name": user.company_name,
            "preferred_language": user.preferred_language,
            "employee_id": user.employee_id,
            "employee_type": user.employee_type,
            "account_enabled": user.account_enabled,
            "age_group": user.age_group,
            "manager_id": manager_id,
        }


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

    # Process users in batches to reduce memory consumption
    batch_size = (
        500  # Process users in larger batches since they're simpler than groups
    )
    users_batch = []

    async for user in get_users(client):
        users_batch.append(user)

        if len(users_batch) >= batch_size:
            transformed_users = list(transform_users(users_batch))
            load_users(neo4j_session, transformed_users, tenant_id, update_tag)
            users_batch.clear()

    # Process any remaining users
    if users_batch:
        transformed_users = list(transform_users(users_batch))
        load_users(neo4j_session, transformed_users, tenant_id, update_tag)

    cleanup(neo4j_session, common_job_parameters)
