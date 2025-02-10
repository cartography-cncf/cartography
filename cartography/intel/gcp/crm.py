# Google Compute Resource Manager
# https://cloud.google.com/resource-manager/docs/cloud-platform-resource-hierarchy
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
def get_gcp_organizations(crm_v1: Resource) -> List[Resource]:
    """
    Return list of GCP organizations that the crm_v1 resource object has permissions to access.
    Returns empty list if we are unable to enumerate organizations for any reason.
    :param crm_v1: The Compute Resource Manager v1 resource object created by `googleapiclient.discovery.build()`.
    See https://googleapis.github.io/google-api-python-client/docs/epy/googleapiclient.discovery-module.html#build.
    :return: List of GCP Organizations. See https://cloud.google.com/resource-manager/reference/rest/v1/organizations.
    """
    try:
        req = crm_v1.organizations().search(body={})
        res = req.execute()
        return res.get("organizations", [])
    except HttpError as e:
        logger.warning(
            "HttpError occurred in crm.get_gcp_organizations(), returning empty list. Details: %r",
            e,
        )
        return []


@timeit
def get_gcp_folders(crm_v2: Resource) -> List[Resource]:
    """
    Return list of GCP folders that the crm_v2 resource object has permissions to access.
    Returns empty list if we are unable to enumerate folders for any reason.
    :param crm_v2: The Compute Resource Manager v2 resource object created by `googleapiclient.discovery.build()`.
    See https://googleapis.github.io/google-api-python-client/docs/epy/googleapiclient.discovery-module.html#build.
    :return: List of GCP folders. See https://cloud.google.com/resource-manager/reference/rest/v2/folders/list.
    """
    try:
        req = crm_v2.folders().search(body={})
        res = req.execute()
        return res.get("folders", [])
    except HttpError as e:
        logger.warning(
            "HttpError occurred in crm.get_gcp_folders(), returning empty list. Details: %r",
            e,
        )
        return []


@timeit
def get_gcp_projects(crm_v1: Resource) -> List[Resource]:
    """
    Return list of GCP projects that the crm_v1 resource object has permissions to access.
    Returns empty list if we are unable to enumerate projects for any reason.
    :param crm_v1: The Compute Resource Manager v1 resource object created by `googleapiclient.discovery.build()`.
    See https://googleapis.github.io/google-api-python-client/docs/epy/googleapiclient.discovery-module.html#build.
    :return: List of GCP projects. See https://cloud.google.com/resource-manager/reference/rest/v2/projects/list.
    """
    try:
        projects: List[Resource] = []
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
def load_gcp_organizations(
    neo4j_session: neo4j.Session,
    data: List[Dict],
    gcp_update_tag: int,
) -> None:
    """
    Ingest the GCP organizations to Neo4j
    :param neo4j_session: The Neo4j session
    :param data: List of organizations; output from crm.get_gcp_organizations()
    :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with
    :return: Nothing
    """
    query = """
    MERGE (org:GCPOrganization{id:$OrgName})
    ON CREATE SET org.firstseen = timestamp()
    SET org.orgname = $OrgName,
    org.displayname = $DisplayName,
    org.lifecyclestate = $LifecycleState,
    org.lastupdated = $gcp_update_tag
    """
    for org_object in data:
        neo4j_session.run(
            query,
            OrgName=org_object["name"],
            DisplayName=org_object.get("displayName", None),
            LifecycleState=org_object.get("lifecycleState", None),
            gcp_update_tag=gcp_update_tag,
        )


@timeit
def load_gcp_folders(
    neo4j_session: neo4j.Session,
    data: List[Dict],
    gcp_update_tag: int,
) -> None:
    """
    Ingest the GCP folders to Neo4j
    :param neo4j_session: The Neo4j session
    :param data: List of folders; output from crm.get_gcp_folders()
    :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with
    :return: Nothing
    """
    for folder in data:
        # Get the correct parent type.
        # Parents of folders can only be GCPOrganizations or other folders, see
        # https://cloud.google.com/resource-manager/docs/cloud-platform-resource-hierarchy
        if folder["parent"].startswith("organizations"):
            query = "MATCH (parent:GCPOrganization{id:$ParentId})"
        elif folder["parent"].startswith("folders"):
            query = """
            MERGE (parent:GCPFolder{id:$ParentId})
            ON CREATE SET parent.firstseen = timestamp()
            """
        query += """
        MERGE (folder:GCPFolder{id:$FolderName})
        ON CREATE SET folder.firstseen = timestamp()
        SET folder.foldername = $FolderName,
        folder.displayname = $DisplayName,
        folder.lifecyclestate = $LifecycleState,
        folder.lastupdated = $gcp_update_tag
        WITH parent, folder
        MERGE (parent)-[r:RESOURCE]->(folder)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $gcp_update_tag
        """
        neo4j_session.run(
            query,
            ParentId=folder["parent"],
            FolderName=folder["name"],
            DisplayName=folder.get("displayName", None),
            LifecycleState=folder.get("lifecycleState", None),
            gcp_update_tag=gcp_update_tag,
        )


@timeit
def load_gcp_projects(
    neo4j_session: neo4j.Session,
    data: List[Dict],
    gcp_update_tag: int,
) -> None:
    """
    Ingest the GCP projects to Neo4j
    :param neo4j_session: The Neo4j session
    :param data: List of GCP projects; output from crm.get_gcp_projects()
    :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with
    :return: Nothing
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
    Attach a project to its respective parent, as in the Resource Hierarchy -
    https://cloud.google.com/resource-manager/docs/cloud-platform-resource-hierarchy
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
def cleanup_gcp_organizations(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict,
) -> None:
    """
    Remove stale GCP organizations and their relationships
    :param neo4j_session: The Neo4j session
    :param common_job_parameters: Parameters to carry to the cleanup job
    :return: Nothing
    """
    run_cleanup_job(
        "gcp_crm_organization_cleanup.json",
        neo4j_session,
        common_job_parameters,
    )


@timeit
def cleanup_gcp_folders(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict,
) -> None:
    """
    Remove stale GCP folders and their relationships
    :param neo4j_session: The Neo4j session
    :param common_job_parameters: Parameters to carry to the cleanup job
    :return: Nothing
    """
    run_cleanup_job("gcp_crm_folder_cleanup.json", neo4j_session, common_job_parameters)


@timeit
def cleanup_gcp_projects(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict,
) -> None:
    """
    Remove stale GCP projects and their relationships
    :param neo4j_session: The Neo4j session
    :param common_job_parameters: Parameters to carry to the cleanup job
    :return: Nothing
    """
    run_cleanup_job(
        "gcp_crm_project_cleanup.json",
        neo4j_session,
        common_job_parameters,
    )


@timeit
def sync_gcp_organizations(
    neo4j_session: neo4j.Session,
    crm_v1: Resource,
    gcp_update_tag: int,
    common_job_parameters: Dict,
) -> None:
    """
    Get GCP organization data using the CRM v1 resource object, load the data to Neo4j, and clean up stale nodes.
    :param neo4j_session: The Neo4j session
    :param crm_v1: The Compute Resource Manager v1 resource object created by `googleapiclient.discovery.build()`.
    See https://googleapis.github.io/google-api-python-client/docs/epy/googleapiclient.discovery-module.html#build.
    :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with
    :param common_job_parameters: Parameters to carry to the Neo4j jobs
    :return: Nothing
    """
    logger.debug("Syncing GCP organizations")
    data = get_gcp_organizations(crm_v1)
    load_gcp_organizations(neo4j_session, data, gcp_update_tag)
    cleanup_gcp_organizations(neo4j_session, common_job_parameters)


@timeit
def sync_gcp_folders(
    neo4j_session: neo4j.Session,
    crm_v2: Resource,
    gcp_update_tag: int,
    common_job_parameters: Dict,
) -> None:
    """
    Get GCP folder data using the CRM v2 resource object, load the data to Neo4j, and clean up stale nodes.
    :param neo4j_session: The Neo4j session
    :param crm_v2: The Compute Resource Manager v2 resource object created by `googleapiclient.discovery.build()`.
    See https://googleapis.github.io/google-api-python-client/docs/epy/googleapiclient.discovery-module.html#build.
    :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with
    :param common_job_parameters: Parameters to carry to the Neo4j jobs
    :return: Nothing
    """
    logger.debug("Syncing GCP folders")
    folders = get_gcp_folders(crm_v2)
    load_gcp_folders(neo4j_session, folders, gcp_update_tag)
    cleanup_gcp_folders(neo4j_session, common_job_parameters)


@timeit
def sync_gcp_projects(
    neo4j_session: neo4j.Session,
    projects: List[Dict],
    gcp_update_tag: int,
    common_job_parameters: Dict,
) -> None:
    """
    Load a given list of GCP project data to Neo4j and clean up stale nodes.
    :param neo4j_session: The Neo4j session
    :param projects: List of GCP projects; output from crm.get_gcp_projects()
    :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with
    :param common_job_parameters: Parameters to carry to the Neo4j jobs
    :return: Nothing
    """
    logger.debug("Syncing GCP projects")
    load_gcp_projects(neo4j_session, projects, gcp_update_tag)
    cleanup_gcp_projects(neo4j_session, common_job_parameters)
