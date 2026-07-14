import logging
from typing import Dict
from typing import List
from typing import Optional

import neo4j
from google.api_core.exceptions import Forbidden
from google.api_core.exceptions import NotFound
from google.api_core.exceptions import PermissionDenied
from google.auth.credentials import Credentials as GoogleCredentials
from google.cloud import resourcemanager_v3

from cartography.client.core.tx import load
from cartography.intel.gcp.crm.folders import get_default_apps_script_folder_names
from cartography.models.gcp.crm.projects import GCPProjectSchema
from cartography.models.gcp.crm.projects import GCPStandaloneProjectSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


def _get_project_parents_to_list(
    org_resource_name: str,
    folders: List[Dict],
) -> set[str]:
    """
    Build the parent set for list_projects(), excluding documented default Apps Script folders.
    """
    folder_names = {folder["name"] for folder in folders if folder.get("name")}
    excluded_folder_names = get_default_apps_script_folder_names(folders)
    return {org_resource_name, *folder_names} - excluded_folder_names


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
    parents = _get_project_parents_to_list(org_resource_name, folders)
    results: List[Dict] = []
    client = resourcemanager_v3.ProjectsClient(credentials=credentials)
    for parent in sorted(parents):
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
def transform_gcp_projects(
    data: List[Dict],
    warn_on_missing_parent: bool = True,
) -> List[Dict]:
    """
    Transform GCP project data to add parent_org or parent_folder fields based on parent type.

    :param data: List of project dicts
    :param warn_on_missing_parent: Whether to warn when a project has no parent. True for
        the org-based sync path, where every project is discovered under an organization or
        folder so an empty parent is unexpected. False for the standalone (``--gcp-project-ids``)
        path, where a project legitimately may not belong to any org or folder.
    :return: List of transformed project dicts with parent_org and parent_folder fields
    """
    for project in data:
        project["parent_org"] = None
        project["parent_folder"] = None

        # Set parent fields based on parent type. A standalone project synced
        # directly by ID may have no parent at all (it does not belong to an org
        # or folder), in which case both fields stay None and no PARENT edge is
        # created.
        parent = project.get("parent") or ""
        if parent.startswith("organizations"):
            project["parent_org"] = parent
        elif parent.startswith("folders"):
            project["parent_folder"] = parent
        elif parent:
            logger.warning(
                f"Project {project['projectId']} has unexpected parent type: {parent}"
            )
        elif warn_on_missing_parent:
            # Empty parent in the org-based path is unexpected: list_projects()
            # walks the org/folder hierarchy, so every project should have one.
            # The standalone path passes warn_on_missing_parent=False because a
            # parentless project is normal there.
            logger.warning(
                "Project %s has no parent; expected an organization or folder "
                "in the org-based sync path.",
                project["projectId"],
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


@timeit
def get_gcp_projects_by_ids(
    project_ids: List[str],
    credentials: Optional[GoogleCredentials] = None,
) -> List[Dict]:
    """
    Fetch specific GCP projects directly by project ID, bypassing organization and
    folder discovery.

    Unlike get_gcp_projects(), which lists projects under an organization hierarchy,
    this uses get_project() so it works for any project the caller can access -
    including projects that do not belong to a GCP Organization.

    A single inaccessible or misspelled project ID does not abort the whole run: it is
    logged and skipped so the remaining projects still sync. (Transient errors are not
    caught here and still propagate.)

    Note that get_project() returns a project in any lifecycle state, whereas the
    org-based path relies on list_projects() returning only ACTIVE projects. To keep
    the two paths consistent, non-ACTIVE projects (e.g. DELETE_REQUESTED) are skipped
    with a warning rather than ingested as live GCPProjects.

    Because both inaccessible/missing IDs and non-ACTIVE projects are skipped, the
    returned list may be shorter than project_ids.

    :param project_ids: List of GCP project IDs (e.g. ["my-project-1", "my-project-2"]).
    :param credentials: GCP credentials to use for API calls.
    :return: List of project dicts matching the shape returned by get_gcp_projects().
    """
    client = resourcemanager_v3.ProjectsClient(credentials=credentials)
    results: List[Dict] = []
    for project_id in project_ids:
        try:
            proj = client.get_project(name=f"projects/{project_id}")
        except (NotFound, PermissionDenied, Forbidden) as e:
            # A single bad ID (misspelled, non-existent, or inaccessible) should not
            # abort the entire sync: log it and continue so the remaining projects
            # still load. Transient errors are intentionally not caught here.
            logger.warning(
                "Skipping GCP project %s: could not fetch it (%s). "
                "Verify the project ID exists and the identity has access.",
                project_id,
                e.__class__.__name__,
            )
            continue
        lifecycle_state = proj.state.name
        # Match org-path semantics (list_projects() only returns ACTIVE): skip
        # projects that are pending deletion or otherwise not ACTIVE so they are
        # not ingested as live projects.
        if lifecycle_state != "ACTIVE":
            logger.warning(
                "Skipping GCP project %s: lifecycle state is %s, not ACTIVE.",
                project_id,
                lifecycle_state,
            )
            continue
        name_field = proj.name  # "projects/<number>"
        project_number = name_field.split("/")[-1] if name_field else None
        results.append(
            {
                "projectId": getattr(proj, "project_id", None),
                "projectNumber": project_number,
                "name": getattr(proj, "display_name", None),
                "lifecycleState": lifecycle_state,
                "parent": getattr(proj, "parent", None),
            }
        )
    return results


@timeit
def load_standalone_gcp_projects(
    neo4j_session: neo4j.Session,
    data: List[Dict],
    gcp_update_tag: int,
) -> None:
    """
    Load GCP projects that were fetched directly by ID (no organization context).

    Uses GCPStandaloneProjectSchema, which has no organization sub-resource
    relationship. Any PARENT edges to a GCPOrganization or GCPFolder are still
    created if those nodes already exist in the graph, but are skipped otherwise.
    """
    # warn_on_missing_parent=False: a standalone project legitimately may have no
    # parent (it does not belong to an org or folder), so a missing parent here is
    # expected and should not emit a warning.
    transformed_data = transform_gcp_projects(data, warn_on_missing_parent=False)
    load(
        neo4j_session,
        GCPStandaloneProjectSchema(),
        transformed_data,
        lastupdated=gcp_update_tag,
    )


@timeit
def sync_gcp_projects_by_ids(
    neo4j_session: neo4j.Session,
    project_ids: List[str],
    gcp_update_tag: int,
    credentials: Optional[GoogleCredentials] = None,
) -> List[Dict]:
    """
    Get and sync specific GCP projects by ID, without organization/folder discovery.

    This powers the standalone single-project sync path. No cleanup job is run for the
    project node itself: a standalone project has no organization sub-resource to scope
    a cleanup against, and running a global cleanup would risk deleting projects synced
    by the organization-based path. Resource-level cleanup (Compute, IAM, etc.) is still
    handled per-project by the individual resource modules, scoped by PROJECT_ID.

    :param project_ids: List of GCP project IDs to sync.
    :return: List of projects synced. An inaccessible or non-existent project ID raises
        (fail loud), but projects that exist in a non-ACTIVE lifecycle state are skipped,
        so the returned list may be shorter than project_ids.
    """
    logger.debug("Syncing GCP projects by id: %s", project_ids)
    projects = get_gcp_projects_by_ids(project_ids, credentials=credentials)
    load_standalone_gcp_projects(neo4j_session, projects, gcp_update_tag)
    return projects
