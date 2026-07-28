import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.supabase.util import epoch_ms_to_datetime
from cartography.intel.supabase.util import get_json
from cartography.intel.supabase.util import iso_to_datetime
from cartography.intel.supabase.util import TOLERATED_STATUSES
from cartography.intel.supabase.util import warn_unavailable
from cartography.models.supabase.edgefunction import SupabaseEdgeFunctionSchema
from cartography.models.supabase.secret import SupabaseSecretSchema
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

    edge_functions = get(api_session, base_url, project_ref)
    if edge_functions is None:
        warn_unavailable("edge functions", project_ref)
    else:
        load_edge_functions(
            neo4j_session,
            transform_edge_functions(edge_functions),
            project_ref,
            update_tag,
        )
        cleanup_edge_functions(neo4j_session, common_job_parameters)

    secrets = get_secrets(api_session, base_url, project_ref)
    if secrets is None:
        warn_unavailable("function secrets", project_ref)
    else:
        load_secrets(
            neo4j_session,
            transform_secrets(secrets, project_ref),
            project_ref,
            update_tag,
        )
        cleanup_secrets(neo4j_session, common_job_parameters)


@timeit
def get(
    api_session: requests.Session,
    base_url: str,
    project_ref: str,
) -> list[dict[str, Any]]:
    return get_json(
        api_session,
        f"{base_url}/v1/projects/{project_ref}/functions",
        tolerate=TOLERATED_STATUSES,
    )


@timeit
def get_secrets(
    api_session: requests.Session,
    base_url: str,
    project_ref: str,
) -> list[dict[str, Any]]:
    """
    List the project's function secrets.

    NOTE: this response carries a `value` field holding the secret material. It is
    dropped in transform_secrets and never written to the graph.
    """
    return get_json(
        api_session,
        f"{base_url}/v1/projects/{project_ref}/secrets",
        tolerate=TOLERATED_STATUSES,
    )


def transform_edge_functions(
    edge_functions: list[dict[str, Any]] | None,
) -> list[dict[str, Any]]:
    return [
        {
            "id": fn["id"],
            "slug": fn["slug"],
            "name": fn["name"],
            "status": fn["status"],
            "version": fn["version"],
            "verify_jwt": fn.get("verify_jwt"),
            "import_map": fn.get("import_map"),
            "entrypoint_path": fn.get("entrypoint_path"),
            "import_map_path": fn.get("import_map_path"),
            # Unlike the rest of the Management API, the functions endpoints return
            # epoch milliseconds rather than ISO-8601 strings.
            "created_at": epoch_ms_to_datetime(fn["created_at"]),
            "updated_at": epoch_ms_to_datetime(fn["updated_at"]),
        }
        for fn in edge_functions or []
    ]


def transform_secrets(
    secrets: list[dict[str, Any]] | None,
    project_ref: str,
) -> list[dict[str, Any]]:
    return [
        {
            "id": f"{project_ref}/{secret['name']}",
            "name": secret["name"],
            "updated_at": iso_to_datetime(secret.get("updated_at")),
        }
        for secret in secrets or []
    ]


@timeit
def load_edge_functions(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    project_ref: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        SupabaseEdgeFunctionSchema(),
        data,
        lastupdated=update_tag,
        PROJECT_REF=project_ref,
    )


@timeit
def load_secrets(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    project_ref: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        SupabaseSecretSchema(),
        data,
        lastupdated=update_tag,
        PROJECT_REF=project_ref,
    )


@timeit
def cleanup_edge_functions(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(
        SupabaseEdgeFunctionSchema(),
        common_job_parameters,
    ).run(neo4j_session)


@timeit
def cleanup_secrets(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(SupabaseSecretSchema(), common_job_parameters).run(
        neo4j_session,
    )
