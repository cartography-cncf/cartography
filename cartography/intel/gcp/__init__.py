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
from cartography.intel.gcp.clients import build_client
from cartography.intel.gcp.crm.folders import sync_gcp_folders
from cartography.intel.gcp.crm.orgs import sync_gcp_organizations
from cartography.intel.gcp.crm.projects import get_gcp_projects
from cartography.intel.gcp.crm.projects import sync_gcp_projects
from cartography.util import run_analysis_job
from cartography.util import timeit

logger = logging.getLogger(__name__)

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


def _sync_multiple_projects(
    neo4j_session: neo4j.Session,
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
    # Per-project sync across services
    for project in projects:
        project_id = project["projectId"]
        common_job_parameters["PROJECT_ID"] = project_id
        enabled_services = _services_enabled_on_project(
            build_client("serviceusage", "v1"), project_id
        )

        if service_names.compute in enabled_services:
            logger.info("Syncing GCP project %s for Compute.", project_id)
            compute_cred = build_client("compute", "v1")
            compute.sync(
                neo4j_session,
                compute_cred,
                project_id,
                gcp_update_tag,
                common_job_parameters,
            )

        if service_names.storage in enabled_services:
            logger.info("Syncing GCP project %s for Storage.", project_id)
            storage_cred = build_client("storage", "v1")
            storage.sync_gcp_buckets(
                neo4j_session,
                storage_cred,
                project_id,
                gcp_update_tag,
                common_job_parameters,
            )

        if service_names.gke in enabled_services:
            logger.info("Syncing GCP project %s for GKE.", project_id)
            container_cred = build_client("container", "v1")
            gke.sync_gke_clusters(
                neo4j_session,
                container_cred,
                project_id,
                gcp_update_tag,
                common_job_parameters,
            )

        if service_names.dns in enabled_services:
            logger.info("Syncing GCP project %s for DNS.", project_id)
            dns_cred = build_client("dns", "v1")
            dns.sync(
                neo4j_session,
                dns_cred,
                project_id,
                gcp_update_tag,
                common_job_parameters,
            )

        if service_names.iam in enabled_services:
            logger.info("Syncing GCP project %s for IAM.", project_id)
            iam_cred = build_client("iam", "v1")
            iam.sync(
                neo4j_session,
                iam_cred,
                project_id,
                gcp_update_tag,
                common_job_parameters,
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

    try:
        crm_v1 = build_client("cloudresourcemanager", "v1")
        crm_v2 = build_client("cloudresourcemanager", "v2")
    except RuntimeError as e:
        logger.warning(f"Unable to initialize GCP clients; skipping module: {e}")
        return

    # If we don't have perms to pull Orgs or Folders from GCP, we will skip safely
    sync_gcp_organizations(
        neo4j_session, crm_v1, config.update_tag, common_job_parameters
    )
    sync_gcp_folders(neo4j_session, crm_v2, config.update_tag, common_job_parameters)

    projects = get_gcp_projects(crm_v1)

    _sync_multiple_projects(
        neo4j_session, projects, config.update_tag, common_job_parameters
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
