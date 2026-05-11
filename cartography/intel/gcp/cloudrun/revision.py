import logging
import re

import neo4j
from google.auth.credentials import Credentials as GoogleCredentials

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.gcp.clients import build_cloud_run_revision_client
from cartography.intel.gcp.cloudrun.util import fetch_cloud_run_resources_for_locations
from cartography.intel.gcp.cloudrun.util import list_cloud_run_resources_for_location
from cartography.models.gcp.cloudrun.revision import GCPCloudRunRevisionSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_revisions(
    project_id: str,
    locations: list[str],
    credentials: GoogleCredentials,
) -> list[dict]:
    """
    Get GCP Cloud Run Revisions for a project across cached locations.
    """

    client = build_cloud_run_revision_client(credentials=credentials)

    def fetch_for_location(location: str) -> list[dict]:
        return list_cloud_run_resources_for_location(
            fetcher=lambda **kw: client.list_revisions(
                parent=f"{location}/services/-",
                **kw,
            ),
            resource_type="revisions",
            location=location,
            project_id=project_id,
        )

    return fetch_cloud_run_resources_for_locations(
        locations=locations,
        project_id=project_id,
        resource_type="revisions",
        fetch_for_location=fetch_for_location,
    )


def transform_revisions(revisions_data: list[dict], project_id: str) -> list[dict]:
    """
    Transform the list of Cloud Run Revision dicts into revision-level records.
    Revisions are pure versioning markers; per-container image data lives on the
    parent Service's GCPCloudRunContainer children (latestReadyRevision).
    """
    transformed: list[dict] = []
    for revision in revisions_data:
        full_name = revision["name"]

        name_match = re.match(
            r"projects/[^/]+/locations/([^/]+)/services/([^/]+)/revisions/([^/]+)",
            full_name,
        )
        location = name_match.group(1) if name_match else None
        short_name = name_match.group(3) if name_match else None

        service_name = revision.get("service")
        service_full_name = None
        if isinstance(service_name, str):
            if service_name.startswith("projects/"):
                service_full_name = service_name
            elif location:
                service_full_name = f"projects/{project_id}/locations/{location}/services/{service_name}"

        transformed.append(
            {
                "id": full_name,
                "name": short_name,
                "service": service_full_name,
                "service_account_email": revision.get("serviceAccount"),
                "log_uri": revision.get("logUri"),
                "project_id": project_id,
            },
        )
    return transformed


@timeit
def load_revisions(
    neo4j_session: neo4j.Session,
    data: list[dict],
    project_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        GCPCloudRunRevisionSchema(),
        data,
        lastupdated=update_tag,
        project_id=project_id,
    )


@timeit
def cleanup_revisions(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict,
) -> None:
    GraphJob.from_node_schema(GCPCloudRunRevisionSchema(), common_job_parameters).run(
        neo4j_session,
    )


@timeit
def sync_revisions(
    neo4j_session: neo4j.Session,
    project_id: str,
    update_tag: int,
    common_job_parameters: dict,
    cloud_run_locations: list[str],
    credentials: GoogleCredentials,
) -> None:
    """
    Sync GCP Cloud Run Revisions for a project.
    """
    logger.info("Syncing Cloud Run Revisions for project %s.", project_id)
    revisions_raw = get_revisions(project_id, cloud_run_locations, credentials)
    if not revisions_raw:
        logger.info("No Cloud Run revisions found for project %s.", project_id)

    revisions = transform_revisions(revisions_raw, project_id)
    load_revisions(neo4j_session, revisions, project_id, update_tag)

    cleanup_job_params = common_job_parameters.copy()
    cleanup_job_params["project_id"] = project_id
    cleanup_revisions(neo4j_session, cleanup_job_params)
