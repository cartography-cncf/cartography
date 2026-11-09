import logging
from typing import Any
from typing import AsyncGenerator
from typing import Generator

import neo4j
from kiota_abstractions.api_error import APIError
from msgraph import GraphServiceClient
from msgraph.generated.models.organization import Organization
from msgraph.generated.models.user import User
from msgraph.generated.models.user_registration_details import UserRegistrationDetails

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.microsoft import credentials
from cartography.intel.microsoft.entra.domains import domain_name_of
from cartography.intel.microsoft.entra.utils import call_with_retries
from cartography.intel.microsoft.entra.utils import EMPTY_RISK
from cartography.intel.microsoft.entra.utils import get_optional_id_map
from cartography.intel.microsoft.entra.utils import transform_risk
from cartography.models.microsoft.entra.tenant import EntraTenantSchema
from cartography.models.microsoft.entra.user import EntraUserSchema
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
    "userType",
    "externalUserState",
]

# Optional reports: each needs a permission and license the user inventory does not.
MFA_REGISTRATION_PERMISSION = "AuditLog.Read.All and Entra ID P1/P2 licensing"
RISKY_USERS_PERMISSION = "IdentityRiskyUser.Read.All and Entra ID P2 licensing"


@timeit
async def get_tenant(client: GraphServiceClient) -> Organization:
    """
    Get tenant information from Microsoft Graph API
    """
    org = await call_with_retries(client.organization.get)
    return org.value[0]  # Get the first (and typically only) tenant


@timeit
async def get_users(
    client: GraphServiceClient,
) -> AsyncGenerator[tuple[list[User], bool], None]:
    """Yield user pages and whether the request included sign-in activity.

    We leverage `$expand=manager($select=id)` so the manager's *id* is hydrated
    alongside every user record.  This avoids making a second round-trip per
    user – vastly reducing latency and eliminating the noisy 404s that occur
    when a user has no manager assigned.
    """

    request_configuration = client.users.UsersRequestBuilderGetRequestConfiguration(
        query_parameters=client.users.UsersRequestBuilderGetQueryParameters(
            # Graph caps pages at 500 when signInActivity is selected.
            top=500,
            select=[*USER_SELECT_FIELDS, "signInActivity"],
            expand=["manager($select=id)"],
        ),
    )

    activity_available = True
    try:
        page = await call_with_retries(
            lambda: client.users.get(request_configuration=request_configuration),
        )
    except APIError as error:
        if error.response_status_code != 403:
            raise
        # Activity requires extra permissions/licensing; basic inventory does not.
        logger.warning(
            "Entra user sign-in activity request was forbidden; retrying without "
            "signInActivity. Check AuditLog.Read.All and Entra ID P1/P2 licensing."
        )
        request_configuration.query_parameters.select = USER_SELECT_FIELDS
        request_configuration.query_parameters.top = 999
        activity_available = False
        page = await call_with_retries(
            lambda: client.users.get(request_configuration=request_configuration),
        )

    while page:
        if page.value:
            yield page.value, activity_available
        if not page.odata_next_link:
            break

        try:
            page = await call_with_retries(
                lambda: client.users.with_url(page.odata_next_link).get(),
            )
        except Exception:
            logger.exception("Failed to fetch next page of Entra users")
            raise


def _transform_mfa_registration(
    details: UserRegistrationDetails,
) -> dict[str, Any]:
    return {
        "is_mfa_registered": details.is_mfa_registered,
        "is_mfa_capable": details.is_mfa_capable,
        "mfa_methods_registered": details.methods_registered,
    }


@timeit
async def get_user_mfa_registrations(
    client: GraphServiceClient,
) -> dict[str, dict[str, Any]] | None:
    """Return MFA registration keyed by user ID, or None when Graph denies or throttles it."""
    # The report documents $filter only, so it is read whole rather than with $select.
    builder = client.reports.authentication_methods.user_registration_details
    return await get_optional_id_map(
        builder.get,
        lambda url: builder.with_url(url).get(),
        "user registration details",
        MFA_REGISTRATION_PERMISSION,
        _transform_mfa_registration,
    )


@timeit
async def get_risky_users(
    client: GraphServiceClient,
) -> dict[str, dict[str, Any]] | None:
    """Return risk state keyed by user ID, or None when Graph denies or throttles it."""
    builder = client.identity_protection.risky_users
    return await get_optional_id_map(
        builder.get,
        lambda url: builder.with_url(url).get(),
        "risky users",
        RISKY_USERS_PERMISSION,
        transform_risk,
    )


@timeit
# The manager reference is now embedded in the user objects courtesy of the
# `$expand` we added above, so we no longer need a separate `manager_map`.
def transform_users(
    users: list[User],
    *,
    activity_available: bool,
    mfa_registrations: dict[str, dict[str, Any]] | None = None,
    risky_users: dict[str, dict[str, Any]] | None = None,
) -> Generator[dict[str, Any], None, None]:
    """Convert MS Graph SDK `User` models into dicts matching our schema.

    Each report is None when Graph denied or throttled it, which sets its
    availability flag to false for every user so a null field reads as unknown,
    not as absent.
    """
    mfa_registration_available = mfa_registrations is not None
    mfa_registrations = mfa_registrations or {}
    risk_available = risky_users is not None
    risky_users = risky_users or {}

    for user in users:
        mfa_registration = mfa_registrations.get(user.id or "", {})
        activity = user.sign_in_activity
        manager_id: str | None = None
        if getattr(user, "manager", None) is not None:
            # The SDK materialises `manager` as a DirectoryObject (or subclass)
            manager_id = getattr(user.manager, "id", None)

        yield {
            "id": user.id,
            "user_principal_name": user.user_principal_name,
            "upn_domain": domain_name_of(user.user_principal_name),
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
            "user_type": user.user_type,
            "external_user_state": user.external_user_state,
            "manager_id": manager_id,
            "sign_in_activity_available": activity_available,
            "last_sign_in_date_time": (
                activity.last_sign_in_date_time if activity is not None else None
            ),
            "last_non_interactive_sign_in_date_time": (
                activity.last_non_interactive_sign_in_date_time
                if activity is not None
                else None
            ),
            "last_successful_sign_in_date_time": (
                activity.last_successful_sign_in_date_time
                if activity is not None
                else None
            ),
            "mfa_registration_available": mfa_registration_available,
            "is_mfa_registered": mfa_registration.get("is_mfa_registered"),
            "is_mfa_capable": mfa_registration.get("is_mfa_capable"),
            "mfa_methods_registered": mfa_registration.get("mfa_methods_registered"),
            "risk_available": risk_available,
            **risky_users.get(user.id or "", EMPTY_RISK),
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
    client_id: str | None,
    client_secret: str | None,
    update_tag: int,
    common_job_parameters: dict[str, Any],
    *,
    delegated_auth: bool = False,
    access_token: str | None = None,
) -> None:
    """
    Sync Entra users and tenant information
    :param neo4j_session: Neo4J session for database interface
    :param tenant_id: Entra tenant ID
    :param client_id: Entra application client ID
    :param client_secret: Entra application client secret
    :param update_tag: Timestamp used to determine data freshness
    :param common_job_parameters: dict of other job parameters to carry to sub-jobs
    :param delegated_auth: Use a user's identity and skip cleanup
    :param access_token: Pre-issued Graph access token for delegated auth; the
        current Azure CLI user is used when it is not set
    :return: None
    """
    # Initialize Graph client
    credential = credentials.make_credential(
        tenant_id,
        client_id,
        client_secret,
        delegated_auth=delegated_auth,
        access_token=access_token,
    )
    client = GraphServiceClient(
        credential, scopes=["https://graph.microsoft.com/.default"]
    )

    # Both maps hold a few scalar fields per user, so they are fetched once
    # rather than per page.
    mfa_registrations = await get_user_mfa_registrations(client)
    risky_users = await get_risky_users(client)

    # Keep memory bounded to one Graph page; failures propagate before cleanup.
    async for users, activity_available in get_users(client):
        transformed_users = list(
            transform_users(
                users,
                activity_available=activity_available,
                mfa_registrations=mfa_registrations,
                risky_users=risky_users,
            )
        )
        load_users(neo4j_session, transformed_users, tenant_id, update_tag)

    if not delegated_auth:
        cleanup(neo4j_session, common_job_parameters)
