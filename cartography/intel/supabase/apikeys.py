import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.supabase.util import get_json
from cartography.intel.supabase.util import iso_to_datetime
from cartography.intel.supabase.util import TOLERATED_STATUSES
from cartography.intel.supabase.util import warn_unavailable
from cartography.models.supabase.apikey import SupabaseApiKeySchema
from cartography.models.supabase.signingkey import SupabaseSigningKeySchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    base_url = common_job_parameters["BASE_URL"]
    project_ref = common_job_parameters["PROJECT_REF"]
    update_tag = common_job_parameters["UPDATE_TAG"]

    api_keys = get(api_session, base_url, project_ref)
    if api_keys is None:
        warn_unavailable("API keys", project_ref)
    else:
        load_api_keys(
            neo4j_session,
            transform_api_keys(api_keys, project_ref),
            project_ref,
            update_tag,
        )
        cleanup_api_keys(neo4j_session, common_job_parameters)

    signing_keys = get_signing_keys(api_session, base_url, project_ref)
    if signing_keys is None:
        warn_unavailable("signing keys", project_ref)
    else:
        load_signing_keys(
            neo4j_session,
            transform_signing_keys(signing_keys),
            project_ref,
            update_tag,
        )
        cleanup_signing_keys(neo4j_session, common_job_parameters)


@timeit
def get(
    api_session: requests.Session,
    base_url: str,
    project_ref: str,
) -> list[dict[str, Any]]:
    """
    List the project's API keys.

    NOTE: contrary to what the `reveal` query parameter implies, this endpoint
    returns the full `api_key` value for every key type even when `reveal` is
    omitted, including the `service_role` secret. Verified against the live API.
    `reveal` is still never passed, but the value therefore does reach this
    process: transform_api_keys() builds a fresh dict from an explicit field list
    so it is dropped here and never written to the graph, and the node schema has
    no property to hold it. Do not log this response body.
    """
    return get_json(
        api_session,
        f"{base_url}/v1/projects/{project_ref}/api-keys",
        tolerate=TOLERATED_STATUSES,
    )


@timeit
def get_signing_keys(
    api_session: requests.Session,
    base_url: str,
    project_ref: str,
) -> dict[str, Any]:
    return get_json(
        api_session,
        f"{base_url}/v1/projects/{project_ref}/config/auth/signing-keys",
        tolerate=TOLERATED_STATUSES,
    )


def transform_api_keys(
    api_keys: list[dict[str, Any]] | None,
    project_ref: str,
) -> list[dict[str, Any]]:
    # Only the fields listed below are carried over. In particular the `api_key`
    # value the endpoint returns is dropped here and never reaches the graph.
    result: list[dict[str, Any]] = []
    for key in api_keys or []:
        # Always prefix with the project ref: the API returns "anon" and
        # "service_role" as the ids of the legacy keys, which are identical across
        # every project. Without the prefix two projects would share one node, with
        # each sync overwriting the other's metadata and both projects' RESOURCE
        # edges pointing at it. `id` is also nullable in the spec, hence the type
        # fallback.
        key_id = key.get("id") or key.get("type") or "unknown"
        result.append(
            {
                "id": f"{project_ref}/{key_id}",
                "name": key["name"],
                "type": key.get("type"),
                "prefix": key.get("prefix"),
                "hash": key.get("hash"),
                "description": key.get("description"),
                "inserted_at": iso_to_datetime(key.get("inserted_at")),
                "updated_at": iso_to_datetime(key.get("updated_at")),
            },
        )
    return result


def transform_signing_keys(
    signing_keys: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    return [
        {
            "id": key["id"],
            "algorithm": key.get("algorithm"),
            "status": key.get("status"),
            "created_at": iso_to_datetime(key.get("created_at")),
            "updated_at": iso_to_datetime(key.get("updated_at")),
        }
        for key in (signing_keys or {}).get("keys") or []
    ]


@timeit
def load_api_keys(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    project_ref: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        SupabaseApiKeySchema(),
        data,
        lastupdated=update_tag,
        PROJECT_REF=project_ref,
    )


@timeit
def load_signing_keys(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    project_ref: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        SupabaseSigningKeySchema(),
        data,
        lastupdated=update_tag,
        PROJECT_REF=project_ref,
    )


@timeit
def cleanup_api_keys(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(SupabaseApiKeySchema(), common_job_parameters).run(
        neo4j_session,
    )


@timeit
def cleanup_signing_keys(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(SupabaseSigningKeySchema(), common_job_parameters).run(
        neo4j_session,
    )
