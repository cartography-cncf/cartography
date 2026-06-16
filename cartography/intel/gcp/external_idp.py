import logging
import os
import time
from datetime import datetime
from typing import Dict

import neo4j
import yaml
from google.cloud import storage
from google.cloud.exceptions import NotFound

from cartography.intel.gcp.workspace import cleanup_groups
from cartography.intel.gcp.workspace import cleanup_users
from cartography.intel.gcp.workspace import load_groups
from cartography.intel.gcp.workspace import load_groups_members
from cartography.intel.gcp.workspace import load_users
from cartography.util import timeit

logger = logging.getLogger(__name__)


def download_blob_as_text(bucket_name: str, file_name: str) -> str:
    storage_client: storage.Client = storage.Client()

    try:
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(file_name)
        response = blob.download_as_text()
        return response

    except NotFound as e:
        logger.error(
            f"could not find the blob {file_name} to download. {e}",
            exc_info=True,
            stack_info=True,
        )
        return None

    except Exception as e:
        logger.error(
            f"could not download the blob {file_name}. {e}",
            exc_info=True,
            stack_info=True,
        )
        return None


@timeit
def transform_bucket_file_users(data: str) -> None:
    for user in data.get("Users", []):
        user["id"] = user["email"]
        user["primaryEmail"] = user["email"]
        user["name"] = {
            "fullName": f'{user["firstName"]} {user["lastName"]}',
            "familyName": user["lastName"],
            "givenName": user["firstName"],
        }
        user["creationTime"] = datetime.utcnow()


@timeit
def transform_bucket_file_groups(data: str) -> None:
    for group in data.get("Groups", []):
        group["id"] = group["email"]


@timeit
def transform_bucket_file_memberships(data: str) -> None:
    memberships = {}
    for membership in data.get("Memberships", []):
        members = memberships.get(membership["groupEmail"], [])
        members.append(
            {
                "id": membership["userEmail"],
            },
        )
        memberships[membership["groupEmail"]] = members
    data["Memberships"] = memberships


@timeit
def sync_identites_from_bucket(
    neo4j_session: neo4j.Session, project_id: str, gcp_update_tag: int, common_job_parameters: Dict,
) -> None:
    tic = time.perf_counter()
    bucket_name = os.environ.get("CDX_CUSTOMERS_IDP_BUCKET_NAME")
    file_name = f"{common_job_parameters['WORKSPACE_ID']}/{common_job_parameters['GCP_PROJECT_ID']}/identity.yml"
    data = download_blob_as_text(bucket_name, file_name)
    if not data:
        return
    data = yaml.safe_load(data)

    transform_bucket_file_users(data)
    transform_bucket_file_groups(data)
    transform_bucket_file_memberships(data)

    gcp_organization_id = common_job_parameters['GCP_ORGANIZATION_ID']

    load_users(neo4j_session, data["Users"], gcp_organization_id, gcp_update_tag)
    load_groups(neo4j_session, data["Groups"], gcp_organization_id, gcp_update_tag)

    for group, members in data.get("Memberships", {}).items():
        load_groups_members(neo4j_session, {"id": group}, members, gcp_update_tag)

    cleanup_users(neo4j_session, common_job_parameters)
    cleanup_groups(neo4j_session, common_job_parameters)
    logger.info(f"Time to process GCP external IDP bucket identities for project '{project_id}': {time.perf_counter() - tic:0.4f} seconds")


@timeit
def sync(
    neo4j_session: neo4j.Session, external_idp: Dict, project_id: str, gcp_update_tag: int, common_job_parameters: Dict,
) -> None:
    tic = time.perf_counter()
    logger.info("Syncing Identity data for project '%s' from external Identity '%s'", project_id, external_idp.get("type"))
    if external_idp.get("type") == "BUCKET":
        sync_identites_from_bucket(neo4j_session, project_id, gcp_update_tag, common_job_parameters)
    toc = time.perf_counter()
    logger.info(f"Time to process GCP external IDP for project '{project_id}': {toc - tic:0.4f} seconds")
