import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.supabase.util import get_json
from cartography.intel.supabase.util import iso_to_datetime
from cartography.intel.supabase.util import TOLERATED_STATUSES
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
    load_api_keys(
        neo4j_session,
        transform_api_keys(api_keys, project_ref),
        project_ref,
        update_tag,
    )

    signing_keys = get_signing_keys(api_session, base_url, project_ref)
    load_signing_keys(
        neo4j_session,
        transform_signing_keys(signing_keys),
        project_ref,
        update_tag,
    )

    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(
    api_session: requests.Session,
    base_url: str,
    project_ref: str,
) -> list[dict[str, Any]]:
    """
    List the project's API keys.

    NOTE: `reveal` is deliberately never passed. Without it the API omits the
    `api_key` field, so the key material never reaches this process.
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
    result: list[dict[str, Any]] = []
    for key in api_keys or []:
        # `id` is nullable for the legacy anon / service_role keys, which predate
        # per-key identifiers. Fall back to the project ref plus key type so the
        # node still has a stable identity across syncs.
        key_id = key.get("id") or f"{project_ref}/{key.get('type') or 'unknown'}"
        result.append(
            {
                "id": key_id,
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
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(SupabaseApiKeySchema(), common_job_parameters).run(
        neo4j_session,
    )
    GraphJob.from_node_schema(SupabaseSigningKeySchema(), common_job_parameters).run(
        neo4j_session,
    )
