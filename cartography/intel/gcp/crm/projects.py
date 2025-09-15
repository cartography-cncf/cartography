import logging
from string import Template
from typing import Dict
from typing import List

import neo4j
from googleapiclient.discovery import HttpError
from googleapiclient.discovery import Resource

from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_gcp_projects(crm_v1: Resource) -> List[Dict]:
    """
    Return list of GCP projects that the crm_v1 resource object has permissions to access.
    Returns empty list if we are unable to enumerate projects for any reason.
    :param crm_v1: The Resource Manager v1 resource object.
    :return: List of GCP projects.
    """
    try:
        projects: List[Dict] = []
        req = crm_v1.projects().list(filter="lifecycleState:ACTIVE")
        while req is not None:
            res = req.execute()
            page = res.get("projects", [])
            projects.extend(page)
            req = crm_v1.projects().list_next(
                previous_request=req,
                previous_response=res,
            )
        return projects
    except HttpError as e:
        logger.warning(
            "HttpError occurred in crm.get_gcp_projects(), returning empty list. Details: %r",
            e,
        )
        return []


@timeit
def load_gcp_projects(
    neo4j_session: neo4j.Session,
    data: List[Dict],
    gcp_update_tag: int,
) -> None:
    """
    Ingest the GCP projects to Neo4j.
    """
    query = """
    MERGE (project:GCPProject{id:$ProjectId})
    ON CREATE SET project.firstseen = timestamp()
    SET project.projectid = $ProjectId,
        project.projectnumber = $ProjectNumber,
        project.displayname = $DisplayName,
        project.lifecyclestate = $LifecycleState,
        project.lastupdated = $gcp_update_tag
    """

    for project in data:
        neo4j_session.run(
            query,
            ProjectId=project["projectId"],
            ProjectNumber=project["projectNumber"],
            DisplayName=project.get("name", None),
            LifecycleState=project.get("lifecycleState", None),
            gcp_update_tag=gcp_update_tag,
        )
        if project.get("parent"):
            _attach_gcp_project_parent(neo4j_session, project, gcp_update_tag)


@timeit
def _attach_gcp_project_parent(
    neo4j_session: neo4j.Session,
    project: Dict,
    gcp_update_tag: int,
) -> None:
    """
    Attach a project to its respective parent, as in the Resource Hierarchy.
    """
    if project["parent"]["type"] == "organization":
        parent_label = "GCPOrganization"
    elif project["parent"]["type"] == "folder":
        parent_label = "GCPFolder"
    else:
        raise NotImplementedError(
            "Ingestion of GCP {}s as parent nodes is currently not supported. "
            "Please file an issue at https://github.com/cartography-cncf/cartography/issues.".format(
                project["parent"]["type"],
            ),
        )
    parent_id = f"{project['parent']['type']}s/{project['parent']['id']}"
    INGEST_PARENT_TEMPLATE = Template(
        """
    MATCH (project:GCPProject{id:$ProjectId})

    MERGE (parent:$parent_label{id:$ParentId})
    ON CREATE SET parent.firstseen = timestamp()

    MERGE (parent)-[r:RESOURCE]->(project)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $gcp_update_tag
    """,
    )
    neo4j_session.run(
        INGEST_PARENT_TEMPLATE.safe_substitute(parent_label=parent_label),
        ParentId=parent_id,
        ProjectId=project["projectId"],
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
) -> None:
    """
    Load a given list of GCP project data to Neo4j and clean up stale nodes.
    """
    logger.debug("Syncing GCP projects")
    load_gcp_projects(neo4j_session, projects, gcp_update_tag)
    cleanup_gcp_projects(neo4j_session, common_job_parameters)
