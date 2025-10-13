import logging
from typing import Dict
from typing import List
from typing import Optional

import neo4j
from google.auth.credentials import Credentials as GoogleCredentials
from google.cloud import resourcemanager_v3

from cartography.client.core.tx import load
from cartography.models.gcp.crm.projects import GCPProjectSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_gcp_projects(
    org_resource_name: str,
    folders: List[Dict],
    credentials: Optional[GoogleCredentials] = None,
) -> List[Dict]:
    """
    Return list of ACTIVE GCP projects under the specified organization
    and within the specified folders.
    :param org_resource_name: Full organization resource name (e.g., "organizations/123456789012")
    :param folders: List of folder dictionaries containing 'name' field with full resource names
    """
    folder_names = [folder["name"] for folder in folders] if folders else []
    # Build list of parent resources to check (org and all folders)
    parents = set([org_resource_name] + folder_names)
    results: List[Dict] = []
    for parent in parents:
        client = resourcemanager_v3.ProjectsClient(credentials=credentials)
        for proj in client.list_projects(parent=parent):
            # list_projects returns ACTIVE projects by default
            name_field = proj.name  # "projects/<number>"
            project_number = name_field.split("/")[-1] if name_field else None
            project_parent = proj.parent
            results.append(
                {
                    "projectId": getattr(proj, "project_id", None),
                    "projectNumber": project_number,
                    "name": getattr(proj, "display_name", None),
                    "lifecycleState": proj.state.name,
                    "parent": project_parent,
                }
            )
    return results


@timeit
def transform_gcp_projects(data: List[Dict]) -> List[Dict]:
    """
    Transform GCP project data to add parent_org or parent_folder fields based on parent type.

    :param data: List of project dicts
    :return: List of transformed project dicts with parent_org and parent_folder fields
    """
    for project in data:
        project["parent_org"] = None
        project["parent_folder"] = None

        # Set parent fields based on parent type
        if project["parent"].startswith("organizations"):
            project["parent_org"] = project["parent"]
        elif project["parent"].startswith("folders"):
            project["parent_folder"] = project["parent"]
        else:
            logger.warning(
                f"Project {project['projectId']} has unexpected parent type: {project['parent']}"
            )

    return data


@timeit
def load_gcp_projects(
    neo4j_session: neo4j.Session,
    data: List[Dict],
    gcp_update_tag: int,
    org_resource_name: str,
) -> None:
    """
    Load GCP projects into the graph.
    :param org_resource_name: Full organization resource name (e.g., "organizations/123456789012")
    """
    transformed_data = transform_gcp_projects(data)
    load(
        neo4j_session,
        GCPProjectSchema(),
        transformed_data,
        lastupdated=gcp_update_tag,
        ORG_RESOURCE_NAME=org_resource_name,
    )


@timeit
def sync_gcp_projects(
    neo4j_session: neo4j.Session,
    org_resource_name: str,
    folders: List[Dict],
    gcp_update_tag: int,
    common_job_parameters: Dict,
    credentials: Optional[GoogleCredentials] = None,
) -> List[Dict]:
    """
    Get and sync GCP project data to Neo4j.
    :param org_resource_name: Full organization resource name (e.g., "organizations/123456789012")
    :param folders: List of folder dictionaries containing 'name' field with full resource names
    :return: List of projects synced
    """
    logger.debug("Syncing GCP projects")
    projects = get_gcp_projects(
        org_resource_name,
        folders,
        credentials=credentials,
    )
    load_gcp_projects(neo4j_session, projects, gcp_update_tag, org_resource_name)
    return projects
