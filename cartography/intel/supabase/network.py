import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.supabase.util import get_json
from cartography.intel.supabase.util import TOLERATED_STATUSES
from cartography.intel.supabase.util import warn_unavailable
from cartography.models.supabase.customhostname import SupabaseCustomHostnameSchema
from cartography.models.supabase.pooler import SupabasePoolerSchema
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

    poolers = get(api_session, base_url, project_ref)
    if poolers is None:
        warn_unavailable("connection poolers", project_ref)
    else:
        load_poolers(
            neo4j_session,
            transform_poolers(poolers, project_ref),
            project_ref,
            update_tag,
        )
        cleanup_poolers(neo4j_session, common_job_parameters)

    custom_hostname = get_custom_hostname(api_session, base_url, project_ref)
    if custom_hostname is None:
        warn_unavailable("custom hostname", project_ref)
    else:
        load_custom_hostnames(
            neo4j_session,
            transform_custom_hostname(custom_hostname, project_ref),
            project_ref,
            update_tag,
        )
        cleanup_custom_hostnames(neo4j_session, common_job_parameters)


@timeit
def get(
    api_session: requests.Session,
    base_url: str,
    project_ref: str,
) -> list[dict[str, Any]]:
    """
    Fetch the project's Supavisor connection pooler configuration.

    NOTE: this response carries `connection_string` / `connectionString`, which
    embed credentials. Both are dropped in transform_poolers.
    """
    return get_json(
        api_session,
        f"{base_url}/v1/projects/{project_ref}/config/database/pooler",
        tolerate=TOLERATED_STATUSES,
    )


@timeit
def get_custom_hostname(
    api_session: requests.Session,
    base_url: str,
    project_ref: str,
) -> dict[str, Any]:
    return get_json(
        api_session,
        f"{base_url}/v1/projects/{project_ref}/custom-hostname",
        tolerate=TOLERATED_STATUSES,
    )


def transform_poolers(
    poolers: list[dict[str, Any]] | None,
    project_ref: str,
) -> list[dict[str, Any]]:
    return [
        {
            "id": f"{project_ref}/{pooler['identifier']}",
            "identifier": pooler["identifier"],
            "database_type": pooler.get("database_type"),
            "db_host": pooler.get("db_host"),
            "db_port": pooler.get("db_port"),
            "db_name": pooler.get("db_name"),
            "db_user": pooler.get("db_user"),
            "pool_mode": pooler.get("pool_mode"),
            "is_using_scram_auth": pooler.get("is_using_scram_auth"),
            "default_pool_size": pooler.get("default_pool_size"),
            "max_client_conn": pooler.get("max_client_conn"),
            "database_id": f"{project_ref}/postgres",
        }
        for pooler in poolers or []
    ]


def transform_custom_hostname(
    custom_hostname: dict[str, Any] | None,
    project_ref: str,
) -> list[dict[str, Any]]:
    if not custom_hostname:
        return []
    hostname = custom_hostname.get("custom_hostname")
    if not hostname:
        # The endpoint answers 200 with an empty config when no custom hostname
        # has been set up for the project.
        return []

    result = (custom_hostname.get("data") or {}).get("result") or {}
    return [
        {
            "id": f"{project_ref}/{hostname}",
            "hostname": hostname,
            "type": "CNAME",
            "status": custom_hostname.get("status"),
            "ssl_status": (result.get("ssl") or {}).get("status"),
            "verification_errors": result.get("verification_errors"),
            "custom_origin_server": result.get("custom_origin_server"),
        },
    ]


@timeit
def load_poolers(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    project_ref: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        SupabasePoolerSchema(),
        data,
        lastupdated=update_tag,
        PROJECT_REF=project_ref,
    )


@timeit
def load_custom_hostnames(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    project_ref: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        SupabaseCustomHostnameSchema(),
        data,
        lastupdated=update_tag,
        PROJECT_REF=project_ref,
    )


@timeit
def cleanup_poolers(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(SupabasePoolerSchema(), common_job_parameters).run(
        neo4j_session,
    )


@timeit
def cleanup_custom_hostnames(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(
        SupabaseCustomHostnameSchema(),
        common_job_parameters,
    ).run(neo4j_session)
