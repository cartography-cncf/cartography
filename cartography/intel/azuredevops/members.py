import logging
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

import neo4j

from .util import call_azure_devops_api
from .util import call_azure_devops_api_pagination
from .util import validate_user_data
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


def transform_user(user_data: Dict) -> Dict:
    """
    Transforms the user data from the API into a flattened dictionary.
    """
    transformed = {
        "id": user_data.get("id"),
        "lastAccessedDate": user_data.get("lastAccessedDate"),
    }

    user = user_data.get("user", {})
    transformed["displayName"] = user.get("displayName")
    transformed["principalName"] = user.get("principalName")
    transformed["origin"] = user.get("origin")
    transformed["originId"] = user.get("originId")

    access_level = user_data.get("accessLevel", {})
    transformed["licensingSource"] = access_level.get("licensingSource")
    transformed["status"] = access_level.get("status")

    return transformed


@timeit
def get_users(api_url: str, organization_name: str, access_token: str) -> List[Dict]:
    """
    Retrieve a list of users from the given Azure DevOps organization
    The User Entitlements API is on a different subdomain 'vsaex.dev.azure.com'

    Args:
        api_url: Base Azure DevOps URL (e.g., https://dev.azure.com) - not used for this endpoint
        organization_name: Name of the organization
        access_token: Microsoft Entra ID OAuth access token

    Returns:
        List of user dictionaries or empty list if failed
    """
    # Note: The User Entitlements API is on a different subdomain `vsaex.dev.azure.com`
    url = f"https://vsaex.dev.azure.com/{organization_name}/_apis/userentitlements"
    params = {"api-version": "7.1"}

    logger.debug(f"Fetching all users from: {url}")
    users_response = call_azure_devops_api_pagination(url, access_token, params)

    if not users_response:
        logger.warning(
            f"No response received for users in organization {organization_name}",
        )
        return []

    users = (
        users_response.get("items", [])
        if isinstance(users_response, dict)
        else users_response
    )
    # Filter out invalid users
    valid_users = [u for u in users if validate_user_data(u)]

    if len(valid_users) != len(users):
        logger.warning(
            f"Filtered out {len(users) - len(valid_users)} invalid users for organization {organization_name}",
        )

    logger.debug(
        f"Retrieved {len(valid_users)} valid users for organization {organization_name}",
    )
    return valid_users


@timeit
def load_users(
    neo4j_session: neo4j.Session,
    user_data: List[Dict],
    org_name: str,
    common_job_parameters: Dict[str, Any],
) -> None:
    """
    Load Azure DevOps user data into Neo4j with comprehensive properties.
    - id: User ID (unique identifier)
    - name: Display name
    - principalName: Principal name (email/UPN)
    - origin: User origin (Azure AD, etc.)
    - originId: Origin-specific ID
    - lastAccessDate: Last access date
    - accessLevel: Access level/licensing source
    - status: User status
    - member: Membership information
    - groupEntitlements: Group entitlements (if available)
    """
    query = """
    UNWIND $UserData as user

    MERGE (u:AzureDevOpsUser{id: user.id})
    ON CREATE SET u.firstseen = timestamp()
    SET u.name = user.displayName,
        u.principal_name = user.principalName,
        u.origin = user.origin,
        u.origin_id = user.originId,
        u.last_access_date = user.lastAccessedDate,
        u.access_level = user.licensingSource,
        u.status = user.status,
        u.member = user.member,
        u.group_entitlements = user.groupEntitlements,
        u.lastupdated = $UpdateTag
    WITH u

    MATCH (org:AzureDevOpsOrganization{id: $OrganizationName})
    MERGE (u)-[r:MEMBER_OF]->(org)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $UpdateTag
    """
    neo4j_session.run(
        query,
        UserData=user_data,
        OrganizationName=org_name,
        UpdateTag=common_job_parameters["UPDATE_TAG"],
    )


@timeit
def cleanup(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job(
        "azure_devops_members_cleanup.json", neo4j_session, common_job_parameters,
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict[str, Any],
    access_token: str,
    url: str,
    org_name: str,
) -> None:
    """
    Syncs the users for the given Azure DevOps organization.
    """
    logger.info(f"Syncing users for organization '{org_name}'")
    users = get_users(url, org_name, access_token)
    if users:
        transformed_users = [transform_user(user_data) for user_data in users]
        load_users(neo4j_session, transformed_users, org_name, common_job_parameters)
        cleanup(neo4j_session, common_job_parameters)
    logger.info(f"Processed {len(users) if users else 0} users for org '{org_name}'")
