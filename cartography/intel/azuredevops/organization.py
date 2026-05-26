import logging
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

import neo4j

from .util import call_azure_devops_api
from .util import validate_organization_data
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_organization(api_url: str, organization_name: str, access_token: str) -> Dict:
    """
    Retrieve Azure DevOps organization information
    Args:
        api_url: Base Azure DevOps URL (e.g., https://dev.azure.com)
        organization_name: Name of the organization
        access_token: Microsoft Entra ID OAuth access token

    Returns:
        Dict containing organization data or empty dict if failed
    """
    url = f"{api_url}/{organization_name}/_apis/projects"
    params = {"api-version": "7.1"}

    logger.debug(f"Fetching organization data from: {url}")
    response = call_azure_devops_api(url, access_token, params=params)

    if response and validate_organization_data(response):
        logger.debug(
            f"Successfully retrieved organization data for: {organization_name}",
        )
        return response

    logger.warning(f"Invalid organization data received for {organization_name}")
    return {}


@timeit
def load_organization(
    neo4j_session: neo4j.Session,
    org_data: Dict,
    common_job_parameters: Dict[str, Any],
) -> None:
    """
    Load Azure DevOps organization data into Neo4j with comprehensive properties.

    Properties mapped from Azure DevOps API:
    - id: Organization name (unique identifier)
    - url: Organization URL
    - status: Organization status
    - type: Organization type
    - description: Organization description (if available)
    - created_date: Organization creation date
    - last_updated: Last update timestamp
    """
    query = """
    MERGE (org:AzureDevOpsOrganization{id: $OrgName})
    ON CREATE SET org.firstseen = timestamp()
    SET org.url = $OrgUrl,
        org.status = $OrgStatus,
        org.type = $OrgType,
        org.description = $OrgDescription,
        org.created_date = $OrgCreatedDate,
        org.lastupdated = $UpdateTag
    WITH org

    MATCH (owner:CloudanixWorkspace{id:$workspace_id})
    MERGE (org)<-[o:OWNER]-(owner)
    ON CREATE SET o.firstseen = timestamp()
    SET o.lastupdated = $UpdateTag;
    """
    neo4j_session.run(
        query,
        OrgName=org_data.get("name"),
        OrgUrl=org_data.get("url"),
        OrgStatus=org_data.get("status"),
        OrgType=org_data.get("type"),
        OrgDescription=org_data.get("description"),
        OrgCreatedDate=org_data.get("createdDate"),
        UpdateTag=common_job_parameters["UPDATE_TAG"],
        workspace_id=common_job_parameters["WORKSPACE_ID"],
    )


@timeit
def cleanup(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job(
        "azure_devops_organization_cleanup.json", neo4j_session, common_job_parameters,
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict[str, Any],
    access_token: str,
    url: str,
    org_name: str,
) -> None:
    logger.info(f"Syncing Azure DevOps Organization '{org_name}'")
    # There is no direct api to get org data
    org_data = {
        "name": org_name,
        "url": f"{url}/{org_name}",
    }
    if org_data:
        load_organization(neo4j_session, org_data, common_job_parameters)
        cleanup(neo4j_session, common_job_parameters)
