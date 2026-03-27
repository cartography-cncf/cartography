import logging
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

import neo4j

from .util import call_azure_devops_api_pagination
from .util import validate_project_data
from cartography.util import normalize_datetime
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_projects(api_url: str, organization_name: str, access_token: str) -> List[Dict]:
    """
    Retrieve a list of projects from the given Azure DevOps organization.

    Args:
        api_url: Base Azure DevOps URL (e.g., https://dev.azure.com)
        organization_name: Name of the organization
        access_token: Microsoft Entra ID OAuth access token

    Returns:
        List of project dictionaries or empty list if failed
    """
    url = f"{api_url}/{organization_name}/_apis/projects"
    params = {"api-version": "7.1"}

    logger.debug(f"Fetching all projects from: {url}")
    projects = call_azure_devops_api_pagination(url, access_token, params)

    if not projects:
        logger.warning(
            f"No response received for projects in organization {organization_name}",
        )
        return []

    # Filter out invalid projects
    valid_projects = [p for p in projects if validate_project_data(p)]

    if len(valid_projects) != len(projects):
        logger.warning(
            f"Filtered out {len(projects) - len(valid_projects)} invalid projects for organization {organization_name}",
        )

    logger.debug(
        f"Retrieved {len(valid_projects)} valid projects for organization {organization_name}",
    )
    return valid_projects


@timeit
def load_projects(
    neo4j_session: neo4j.Session,
    project_data: List[Dict],
    organization_name: str,
    common_job_parameters: Dict[str, Any],
) -> None:
    """
    Load Azure DevOps project data into Neo4j with comprehensive properties.
    - id: Project ID (unique identifier)
    - name: Project name
    - url: Project URL
    - state: Project state (active, deleted, etc.)
    - revision: Project revision number
    - visibility: Project visibility (private, public)
    - is_private: Boolean indicating if the project is private
    - lastUpdateTime: Last update timestamp
    - last_activity_at: Last activity timestamp
    - last_activity_at_timestamp: Last activity timestamp in milliseconds
    - description: Project description (if available)
    - capabilities: Project capabilities (if available)
    """
    query = """
    UNWIND $ProjectData as project

    MERGE (p:AzureDevOpsProject{id: project.id})
    ON CREATE SET p.firstseen = timestamp()
    SET
        p.lastupdated = $UPDATE_TAG,
        p.name = project.name,
        p.url = project.url,
        p.state = project.state,
        p.revision = project.revision,
        p.visibility = project.visibility,
        p.is_private = CASE WHEN project.visibility = 'private' THEN true ELSE false END,
        p.lastupdatetime = project.lastUpdateTime,
        p.last_activity_at = project.last_activity_at,
        p.last_activity_at_timestamp = project.last_activity_at_timestamp,
        p.description = project.description,
        p.capabilities = project.capabilities

    WITH p, project
    MATCH (org:AzureDevOpsOrganization{id: $OrganizationName})
    MERGE (org)-[r:HAS_PROJECT]->(p)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $UPDATE_TAG
    """
    neo4j_session.run(
        query,
        ProjectData=project_data,
        OrganizationName=organization_name,
        UPDATE_TAG=common_job_parameters["UPDATE_TAG"],
    )


@timeit
def cleanup(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job(
        "azure_devops_projects_cleanup.json", neo4j_session, common_job_parameters,
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict[str, Any],
    access_token: str,
    azure_devops_url: str,
    organization_name: str,
) -> List[Dict]:
    """
    Syncs the projects for the given Azure DevOps organization and returns the data.
    """
    logger.info(f"Syncing projects for organization '{organization_name}'")
    projects = get_projects(azure_devops_url, organization_name, access_token)
    if projects:
        for project in projects:
            iso_str, ts_ms = normalize_datetime(project.get("lastUpdateTime"))
            project["last_activity_at"] = iso_str
            project["last_activity_at_timestamp"] = ts_ms
        load_projects(neo4j_session, projects, organization_name, common_job_parameters)
        cleanup(neo4j_session, common_job_parameters)
    return projects
