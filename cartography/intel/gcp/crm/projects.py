import logging
from typing import Dict
from typing import List

import neo4j
from google.cloud import resourcemanager_v3

from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_gcp_projects(org_id: str, folder_names: List[str]) -> List[Dict]:
    """
    Return list of ACTIVE GCP projects under the specified organization
    and within the specified folders.
    """
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
    """
    Ingest the GCP projects to Neo4j, attaching to the discovered parent and to the organization.
    """
    for project in data:
        if project["parent"].startswith("organizations"):
            query = "MATCH (parent:GCPOrganization{id:$ParentId})"
        elif project["parent"].startswith("folders"):
            query = "MATCH (parent:GCPFolder{id:$ParentId})"
        query += """
        MERGE (project:GCPProject{id:$ProjectId})
        ON CREATE SET project.firstseen = timestamp()
        SET project.projectid = $ProjectId,
            project.projectnumber = $ProjectNumber,
            project.displayname = $DisplayName,
            project.lifecyclestate = $LifecycleState,
            project.lastupdated = $gcp_update_tag
        WITH parent, project
        MERGE (parent)<-[r:PARENT]-(project)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $gcp_update_tag
        WITH project
        MATCH (org:GCPOrganization{id:$OrgName})
        MERGE (org)-[r2:RESOURCE]->(project)
        ON CREATE SET r2.firstseen = timestamp()
        SET r2.lastupdated = $gcp_update_tag
        """
        neo4j_session.run(
            query,
            ParentId=project["parent"],
            ProjectId=project["projectId"],
            ProjectNumber=project["projectNumber"],
            DisplayName=project.get("name", None),
            LifecycleState=project.get("lifecycleState", None),
            OrgName=f"organizations/{org_id}",
            gcp_update_tag=gcp_update_tag,
        )


@timeit
def cleanup_gcp_projects(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict,
) -> None:
    """
    Remove stale GCP projects and their relationships.
    """
    run_cleanup_job(
        "gcp_crm_project_cleanup.json",
        neo4j_session,
        common_job_parameters,
    )


@timeit
def sync_gcp_projects(
    neo4j_session: neo4j.Session,
    projects: List[Dict],
    gcp_update_tag: int,
    common_job_parameters: Dict,
    org_id: str,
) -> None:
    """
    Load a given list of GCP project data to Neo4j and clean up stale nodes.
    """
    logger.debug("Syncing GCP projects")
    load_gcp_projects(neo4j_session, projects, gcp_update_tag, org_id)
    cleanup_gcp_projects(neo4j_session, common_job_parameters)
