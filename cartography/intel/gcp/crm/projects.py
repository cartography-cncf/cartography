import logging
from typing import Dict
from typing import List

import neo4j
from google.cloud import resourcemanager_v3

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.gcp.crm.projects import GCPProjectSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_gcp_projects(org_id: str, folders: List[Dict]) -> List[Dict]:
    """
    Return list of ACTIVE GCP projects under the specified organization
    and within the specified folders.
    """
    # Extract folder names from the folder data
    folder_names = [folder["name"] for folder in folders] if folders else []
    parents = set([f"organizations/{org_id}"] + folder_names)
    results: List[Dict] = []
    for parent in parents:
        client = resourcemanager_v3.ProjectsClient()
        try:
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
        except Exception as e:
            logger.warning("Listing projects under %s failed: %r", parent, e)
    return results


@timeit
def load_gcp_projects(
    neo4j_session: neo4j.Session,
    data: List[Dict],
    gcp_update_tag: int,
    org_id: str,
) -> None:
    # Transform data to set parent_org or parent_folder based on parent type
    transformed_data = []
    for project in data:
        transformed_project = {
            "projectId": project["projectId"],
            "projectNumber": project.get("projectNumber"),
            "name": project.get("name"),
            "lifecycleState": project.get("lifecycleState"),
            "parent_org": None,
            "parent_folder": None,
        }

        if project["parent"].startswith("organizations"):
            transformed_project["parent_org"] = project["parent"]
        elif project["parent"].startswith("folders"):
            transformed_project["parent_folder"] = project["parent"]
        else:
            logger.warning(
                f"Skipping project {project['projectId']} with unexpected parent type: {project['parent']}"
            )
            continue

        transformed_data.append(transformed_project)

    load(
        neo4j_session,
        GCPProjectSchema(),
        transformed_data,
        lastupdated=gcp_update_tag,
        ORG_ID=f"organizations/{org_id}",
    )


@timeit
def sync_gcp_projects(
    neo4j_session: neo4j.Session,
    org_id: str,
    folders: List[Dict],
    gcp_update_tag: int,
    common_job_parameters: Dict,
) -> List[Dict]:
    """
    Get and sync GCP project data to Neo4j and clean up stale nodes.
    Returns the list of projects synced.
    """
    logger.debug("Syncing GCP projects")
    projects = get_gcp_projects(org_id, folders)
    load_gcp_projects(neo4j_session, projects, gcp_update_tag, org_id)
    GraphJob.from_node_schema(GCPProjectSchema(), common_job_parameters).run(
        neo4j_session
    )
    return projects
