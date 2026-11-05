import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.neon.util import get_json
from cartography.intel.neon.util import iso_to_datetime
from cartography.intel.neon.util import TOLERATED_STATUSES
from cartography.intel.neon.util import warn_unavailable
from cartography.models.neon.credential import NeonCredentialSchema
from cartography.models.neon.storagebucket import NeonStorageBucketSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    branches: list[dict[str, Any]],
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Sync Neon Object Storage buckets and scoped credentials on every branch of the
    project in scope.

    Both endpoints are in Beta. When either listing is unreadable on any branch,
    its project-scoped cleanup is skipped: the cleanup would otherwise treat that
    branch's buckets or credentials as deleted.
    """
    base_url = common_job_parameters["BASE_URL"]
    project_id = common_job_parameters["PROJECT_ID"]
    update_tag = common_job_parameters["UPDATE_TAG"]

    buckets: list[dict[str, Any]] = []
    credentials: dict[str, dict[str, Any]] = {}
    buckets_complete = True
    credentials_complete = True

    for branch in branches:
        branch_id = branch["id"]
        branch_buckets = get_buckets(api_session, base_url, project_id, branch_id)
        if branch_buckets is None:
            buckets_complete = False
        elif branch_buckets:
            storage = get_storage(api_session, base_url, project_id, branch_id) or {}
            buckets.extend(transform_buckets(branch_buckets, branch_id, storage))

        branch_credentials = get_credentials(
            api_session,
            base_url,
            project_id,
            branch_id,
        )
        if branch_credentials is None:
            credentials_complete = False
            continue
        # A child branch lists the credentials it inherits from its ancestors, with
        # the ancestor's branch_id. Keyed by token id, each appears once.
        for record in transform_credentials(branch_credentials, branch_id):
            credentials[record["token_id"]] = record

    load(
        neo4j_session,
        NeonStorageBucketSchema(),
        buckets,
        lastupdated=update_tag,
        PROJECT_ID=project_id,
    )
    if buckets_complete:
        GraphJob.from_node_schema(
            NeonStorageBucketSchema(),
            common_job_parameters,
        ).run(neo4j_session)
    else:
        warn_unavailable("object storage buckets", project_id)

    load(
        neo4j_session,
        NeonCredentialSchema(),
        list(credentials.values()),
        lastupdated=update_tag,
        PROJECT_ID=project_id,
    )
    if credentials_complete:
        GraphJob.from_node_schema(NeonCredentialSchema(), common_job_parameters).run(
            neo4j_session,
        )
    else:
        warn_unavailable("credentials", project_id)


@timeit
def get_buckets(
    api_session: requests.Session,
    base_url: str,
    project_id: str,
    branch_id: str,
) -> list[dict[str, Any]] | None:
    response = get_json(
        api_session,
        f"{base_url}/projects/{project_id}/branches/{branch_id}/buckets",
        tolerate=TOLERATED_STATUSES,
    )
    if response is None:
        return None
    return response.get("buckets") or []


@timeit
def get_storage(
    api_session: requests.Session,
    base_url: str,
    project_id: str,
    branch_id: str,
) -> dict[str, Any] | None:
    return get_json(
        api_session,
        f"{base_url}/projects/{project_id}/branches/{branch_id}/storage",
        tolerate=TOLERATED_STATUSES,
    )


@timeit
def get_credentials(
    api_session: requests.Session,
    base_url: str,
    project_id: str,
    branch_id: str,
) -> list[dict[str, Any]] | None:
    response = get_json(
        api_session,
        f"{base_url}/projects/{project_id}/branches/{branch_id}/credentials",
        tolerate=TOLERATED_STATUSES,
    )
    if response is None:
        return None
    return response.get("credentials") or []


def transform_buckets(
    buckets: list[dict[str, Any]],
    branch_id: str,
    storage: dict[str, Any],
) -> list[dict[str, Any]]:
    s3_endpoint = (storage.get("s3_endpoint") or "").rstrip("/") or None
    result: list[dict[str, Any]] = []
    for bucket in buckets:
        public = bucket.get("access_level") == "public_read"
        result.append(
            {
                "id": f"{branch_id}/{bucket['name']}",
                "name": bucket["name"],
                "branch_id": branch_id,
                "access_level": bucket.get("access_level"),
                "public": public,
                "exposed_internet": public,
                "exposed_internet_type": ["direct"] if public else None,
                "s3_endpoint": s3_endpoint,
                "url": f"{s3_endpoint}/{bucket['name']}" if s3_endpoint else None,
                "region": storage.get("region"),
                "created_at": iso_to_datetime(bucket.get("created_at")),
            },
        )
    return result


def transform_credentials(
    credentials: list[dict[str, Any]],
    listed_on_branch_id: str,
) -> list[dict[str, Any]]:
    # Build each record from an explicit field list so no secret a future API
    # version might add to this response can reach the graph.
    result: list[dict[str, Any]] = []
    for credential in credentials:
        scopes = credential.get("scopes") or []
        result.append(
            {
                "token_id": credential["token_id"],
                "token_id_short": credential.get("token_id_short"),
                "name": credential.get("name"),
                "scopes": scopes,
                "can_write_storage": "storage:write" in scopes,
                "branch_id": credential.get("branch_id") or listed_on_branch_id,
                "principal_type": credential.get("principal_type"),
                "function_id": credential.get("function_id"),
                "created_at": iso_to_datetime(credential.get("created_at")),
                "last_used_at": iso_to_datetime(credential.get("last_used_at")),
                "expires_at": iso_to_datetime(credential.get("expires_at")),
                "revoked_at": iso_to_datetime(credential.get("revoked_at")),
            },
        )
    return result
