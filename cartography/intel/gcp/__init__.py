import json
import logging
from collections import namedtuple
from typing import Dict
from typing import List
from typing import Set

import neo4j
from googleapiclient.discovery import HttpError
from googleapiclient.discovery import Resource

from cartography.config import Config
from cartography.intel.gcp import compute
from cartography.intel.gcp import dns
from cartography.intel.gcp import gke
from cartography.intel.gcp import iam
from cartography.intel.gcp import storage
from cartography.intel.gcp.clients import build_compute_client
from cartography.intel.gcp.clients import build_container_client
from cartography.intel.gcp.clients import build_dns_client
from cartography.intel.gcp.clients import build_iam_client
from cartography.intel.gcp.clients import build_storage_client
from cartography.intel.gcp.clients import get_gcp_credentials
from cartography.intel.gcp.clients import initialize_clients
from cartography.intel.gcp.crm.folders import sync_gcp_folders
from cartography.intel.gcp.crm.orgs import sync_gcp_organizations
from cartography.intel.gcp.crm.projects import get_gcp_projects
from cartography.intel.gcp.crm.projects import sync_gcp_projects
from cartography.util import run_analysis_job
from cartography.util import timeit

logger = logging.getLogger(__name__)
Resources = namedtuple(
    "Resources", "compute container crm_v1 crm_v2 dns storage serviceusage iam"
)

# Mapping of service short names to their full names as in docs. See https://developers.google.com/apis-explorer,
# and https://cloud.google.com/service-usage/docs/reference/rest/v1/services#ServiceConfig
Services = namedtuple("Services", "compute storage gke dns iam")
service_names = Services(
    compute="compute.googleapis.com",
    storage="storage.googleapis.com",
    gke="container.googleapis.com",
    dns="dns.googleapis.com",
    iam="iam.googleapis.com",
)


def _services_enabled_on_project(serviceusage: Resource, project_id: str) -> Set:
    """
    Return a list of all Google API services that are enabled on the given project ID.
    See https://cloud.google.com/service-usage/docs/reference/rest/v1/services/list for data shape.
    :param serviceusage: the serviceusage resource provider. See https://cloud.google.com/service-usage/docs/overview.
    :param project_id: The project ID number to sync.  See  the `projectId` field in
    https://cloud.google.com/resource-manager/reference/rest/v1/projects
    :return: A set of services that are enabled on the project
    """
    try:
        req = serviceusage.services().list(
            parent=f"projects/{project_id}",
            filter="state:ENABLED",
        )
        services = set()
        while req is not None:
            res = req.execute()
            if "services" in res:
                services.update({svc["config"]["name"] for svc in res["services"]})
            req = serviceusage.services().list_next(
                previous_request=req,
                previous_response=res,
            )
        return services
    except HttpError as http_error:
        http_error = json.loads(http_error.content.decode("utf-8"))
        # This is set to log-level `info` because Google creates many projects under the hood that cartography cannot
        # audit (e.g. adding a script to a Google spreadsheet causes a project to get created) and we don't need to emit
        # a warning for these projects.
        logger.info(
            f"HttpError when trying to get enabled services on project {project_id}. "
            f"Code: {http_error['error']['code']}, Message: {http_error['error']['message']}. "
            f"Skipping.",
        )
        return set()


def _sync_single_project_compute(
    neo4j_session: neo4j.Session,
    resources: Resource,
    project_id: str,
    gcp_update_tag: int,
    common_job_parameters: Dict,
) -> None:
    """
    Handles graph sync for a single GCP project on Compute resources.
    :param neo4j_session: The Neo4j session
    :param resources: namedtuple of the GCP resource objects
    :param project_id: The project ID number to sync.  See  the `projectId` field in
    https://cloud.google.com/resource-manager/reference/rest/v1/projects
    :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with
    :param common_job_parameters: Other parameters sent to Neo4j
    :return: Nothing
    """
    # Determine the resources available on the project.
    enabled_services = _services_enabled_on_project(resources.serviceusage, project_id)
    compute_cred = build_compute_client(get_gcp_credentials())
    if service_names.compute in enabled_services:
        compute.sync(
            neo4j_session,
            compute_cred,
            project_id,
            gcp_update_tag,
            common_job_parameters,
        )


def _sync_single_project_storage(
    neo4j_session: neo4j.Session,
    resources: Resource,
    project_id: str,
    gcp_update_tag: int,
    common_job_parameters: Dict,
) -> None:
    """
    Handles graph sync for a single GCP project on Storage resources.
    :param neo4j_session: The Neo4j session
    :param resources: namedtuple of the GCP resource objects
    :param project_id: The project ID number to sync.  See  the `projectId` field in
    https://cloud.google.com/resource-manager/reference/rest/v1/projects
    :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with
    :param common_job_parameters: Other parameters sent to Neo4j
    :return: Nothing
    """
    # Determine the resources available on the project.
    enabled_services = _services_enabled_on_project(resources.serviceusage, project_id)
    storage_cred = build_storage_client(get_gcp_credentials())
    if service_names.storage in enabled_services:
        storage.sync_gcp_buckets(
            neo4j_session,
            storage_cred,
            project_id,
            gcp_update_tag,
            common_job_parameters,
        )


def _sync_single_project_gke(
    neo4j_session: neo4j.Session,
    resources: Resource,
    project_id: str,
    gcp_update_tag: int,
    common_job_parameters: Dict,
) -> None:
    """
    Handles graph sync for a single GCP project GKE resources.
    :param neo4j_session: The Neo4j session
    :param resources: namedtuple of the GCP resource objects
    :param project_id: The project ID number to sync.  See  the `projectId` field in
    https://cloud.google.com/resource-manager/reference/rest/v1/projects
    :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with
    :param common_job_parameters: Other parameters sent to Neo4j
    :return: Nothing
    """
    # Determine the resources available on the project.
    enabled_services = _services_enabled_on_project(resources.serviceusage, project_id)
    container_cred = build_container_client(get_gcp_credentials())
    if service_names.gke in enabled_services:
        gke.sync_gke_clusters(
            neo4j_session,
            container_cred,
            project_id,
            gcp_update_tag,
            common_job_parameters,
        )


def _sync_single_project_dns(
    neo4j_session: neo4j.Session,
    resources: Resource,
    project_id: str,
    gcp_update_tag: int,
    common_job_parameters: Dict,
) -> None:
    """
    Handles graph sync for a single GCP project DNS resources.
    :param neo4j_session: The Neo4j session
    :param resources: namedtuple of the GCP resource objects
    :param project_id: The project ID number to sync.  See  the `projectId` field in
    https://cloud.google.com/resource-manager/reference/rest/v1/projects
    :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with
    :param common_job_parameters: Other parameters sent to Neo4j
    :return: Nothing
    """
    # Determine the resources available on the project.
    enabled_services = _services_enabled_on_project(resources.serviceusage, project_id)
    dns_cred = build_dns_client(get_gcp_credentials())
    if service_names.dns in enabled_services:
        dns.sync(
            neo4j_session,
            dns_cred,
            project_id,
            gcp_update_tag,
            common_job_parameters,
        )


def _sync_single_project_iam(
    neo4j_session: neo4j.Session,
    resources: Resource,
    project_id: str,
    gcp_update_tag: int,
    common_job_parameters: Dict,
) -> None:
    """
    Handles graph sync for a single GCP project's IAM resources.
    :param neo4j_session: The Neo4j session
    :param resources: namedtuple of the GCP resource objects
    :param project_id: The project ID number to sync.  See  the `projectId` field in
    https://cloud.google.com/resource-manager/reference/rest/v1/projects
    :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with
    :param common_job_parameters: Other parameters sent to Neo4j
    :return: Nothing
    """
    # Determine if IAM service is enabled
    enabled_services = _services_enabled_on_project(resources.serviceusage, project_id)
    iam_cred = build_iam_client(get_gcp_credentials())
    if service_names.iam in enabled_services:
        iam.sync(
            neo4j_session, iam_cred, project_id, gcp_update_tag, common_job_parameters
        )


def _sync_multiple_projects(
    neo4j_session: neo4j.Session,
    resources: Resource,
    projects: List[Dict],
    gcp_update_tag: int,
    common_job_parameters: Dict,
) -> None:
    """
    Handles graph sync for multiple GCP projects.
    :param neo4j_session: The Neo4j session
    :param resources: namedtuple of the GCP resource objects
    :param: projects: A list of projects. At minimum, this list should contain a list of dicts with the key "projectId"
     defined; so it would look like this: [{"projectId": "my-project-id-12345"}].
    This is the returned data from `crm.get_gcp_projects()`.
    See https://cloud.google.com/resource-manager/reference/rest/v1/projects.
    :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with
    :param common_job_parameters: Other parameters sent to Neo4j
    :return: Nothing
    """
    logger.info("Syncing %d GCP projects.", len(projects))
    sync_gcp_projects(
        neo4j_session,
        projects,
        gcp_update_tag,
        common_job_parameters,
    )
    # Compute data sync
    for project in projects:
        project_id = project["projectId"]
        common_job_parameters["PROJECT_ID"] = project_id
        logger.info("Syncing GCP project %s for Compute.", project_id)
        _sync_single_project_compute(
            neo4j_session,
            resources,
            project_id,
            gcp_update_tag,
            common_job_parameters,
        )
        del common_job_parameters["PROJECT_ID"]

    # Storage data sync
    for project in projects:
        project_id = project["projectId"]
        common_job_parameters["PROJECT_ID"] = project_id
        logger.info("Syncing GCP project %s for Storage", project_id)
        _sync_single_project_storage(
            neo4j_session,
            resources,
            project_id,
            gcp_update_tag,
            common_job_parameters,
        )
        del common_job_parameters["PROJECT_ID"]

    # GKE data sync
    for project in projects:
        project_id = project["projectId"]
        common_job_parameters["PROJECT_ID"] = project_id
        logger.info("Syncing GCP project %s for GKE", project_id)
        _sync_single_project_gke(
            neo4j_session,
            resources,
            project_id,
            gcp_update_tag,
            common_job_parameters,
        )
        del common_job_parameters["PROJECT_ID"]

    # DNS data sync
    for project in projects:
        project_id = project["projectId"]
        common_job_parameters["PROJECT_ID"] = project_id
        logger.info("Syncing GCP project %s for DNS", project_id)
        _sync_single_project_dns(
            neo4j_session,
            resources,
            project_id,
            gcp_update_tag,
            common_job_parameters,
        )
        del common_job_parameters["PROJECT_ID"]

    # IAM data sync
    for project in projects:
        project_id = project["projectId"]
        common_job_parameters["PROJECT_ID"] = project_id
        logger.info("Syncing GCP project %s for IAM", project_id)
        _sync_single_project_iam(
            neo4j_session, resources, project_id, gcp_update_tag, common_job_parameters
        )
        del common_job_parameters["PROJECT_ID"]


@timeit
def start_gcp_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    """
    Starts the GCP ingestion process by initializing Google Application Default Credentials, creating the necessary
    resource objects, listing all GCP organizations and projects available to the GCP identity, and supplying that
    context to all intel modules.
    :param neo4j_session: The Neo4j session
    :param config: A `cartography.config` object
    :return: Nothing
    """
    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
    }

    credentials = get_gcp_credentials()
    if credentials is None:
        logger.warning("Unable to initialize GCP credentials. Skipping module.")
        return

    resources = initialize_clients(credentials)

    # If we don't have perms to pull Orgs or Folders from GCP, we will skip safely
    sync_gcp_organizations(
        neo4j_session,
        resources.crm_v1,
        config.update_tag,
        common_job_parameters,
    )
    sync_gcp_folders(
        neo4j_session,
        resources.crm_v2,
        config.update_tag,
        common_job_parameters,
    )

    projects = get_gcp_projects(resources.crm_v1)

    _sync_multiple_projects(
        neo4j_session,
        resources,
        projects,
        config.update_tag,
        common_job_parameters,
    )

    run_analysis_job(
        "gcp_compute_asset_inet_exposure.json",
        neo4j_session,
        common_job_parameters,
    )

    run_analysis_job(
        "gcp_gke_asset_exposure.json",
        neo4j_session,
        common_job_parameters,
    )

    run_analysis_job(
        "gcp_gke_basic_auth.json",
        neo4j_session,
        common_job_parameters,
    )
