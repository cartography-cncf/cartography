# Google Compute Resource Manager
# https://cloud.google.com/resource-manager/docs/cloud-platform-resource-hierarchy
import logging
from typing import Dict
from typing import List
from typing import Optional
from typing import Set

import neo4j
from google.cloud import resourcemanager_v3
from googleapiclient.discovery import HttpError
from googleapiclient.discovery import Resource

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.gcp.crm import GCPProjectSchema
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
    # Transform parent hierarchy for relationship creation
    # https://cloud.google.com/resource-manager/docs/cloud-platform-resource-hierarchy
    for project in data:
        parent = project.get("parent")
        # Derive parent_folder if project is in a folder
        if project.get("parent_folder") is None:
            if parent and parent.get("type") == "folder":
                project["parent_folder"] = f"folders/{parent['id']}"

    # Group projects by their organization tenant so that we can pass the ORG_ID kwarg
    projects_by_org: Dict[Optional[str], List[Dict]] = {}
    for p in data:
        org_id = p.get("organization")  # e.g. "organizations/1234567890" or None
        projects_by_org.setdefault(org_id, []).append(p)

    # Load projects per organization to ensure the sub_resource (tenant) relationship is created correctly.
    for org_id, projects in projects_by_org.items():
        if org_id:
            load(
                neo4j_session,
                GCPProjectSchema(),
                projects,
                lastupdated=gcp_update_tag,
                ORG_ID=org_id,
            )
        else:
            # Load projects without an org parent; they will not attach a tenant link.
            # This preserves ingestion behavior for edge cases while allowing most projects to be tenant-scoped.
            load(
                neo4j_session,
                GCPProjectSchema(),
                projects,
                lastupdated=gcp_update_tag,
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
def sync_gcp_organizations(
    neo4j_session: neo4j.Session,
    crm_v1: Resource,
    gcp_update_tag: int,
    common_job_parameters: Dict,
) -> Set[str]:
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
    # Return set of organization resource names, e.g., {'organizations/123456789012'}
    org_ids: Set[str] = set()
    for org in data:
        name = org.get("name")
        if name:
            org_ids.add(name)
    return org_ids


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
    org_ids: Optional[Set[str]],
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

    # If no orgs discovered, skip scoped cleanup (nothing to scope by)
    if org_ids is None:
        return

    for org_id in org_ids:
        params = dict(common_job_parameters)
        params["ORG_ID"] = org_id
        GraphJob.from_node_schema(GCPProjectSchema(), params).run(neo4j_session)


@timeit
def get_gcp_projects_for_org_v3(org_numeric_id: str) -> List[Dict]:
    """
    Return list of GCP projects that are descendants of the given organization using the
    google-cloud-resource-manager v3 client. This traverses folders under the org.

    If the v3 client is not available, returns an empty list.
    :param org_numeric_id: The numeric organization ID, e.g., "123456789012"
    :return: List of project dicts with at least 'projectId' and 'projectNumber'.
    """
    client = resourcemanager_v3.ProjectsClient()

    query = f"parent.type:organization parent.id:{org_numeric_id} state:ACTIVE"
    request = resourcemanager_v3.SearchProjectsRequest(query=query)

    projects: List[Dict] = []
    for p in client.search_projects(request=request):
        # p.name is like 'projects/<number>'
        number = p.name.split("/")[-1] if p.name else None
        projects.append(
            {
                "projectId": p.project_id,
                "projectNumber": number,
                "name": p.display_name,
                # Mark org tenant explicitly; caller can use this directly
                "organization": f"organizations/{org_numeric_id}",
            }
        )
    return projects
