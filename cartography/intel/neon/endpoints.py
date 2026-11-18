import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.neon.util import get_json
from cartography.intel.neon.util import iso_to_datetime
from cartography.models.neon.endpoint import NeonEndpointSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

_ANY_ADDRESS = {"0.0.0.0/0", "::/0", "0.0.0.0-255.255.255.255"}


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    project: dict[str, Any],
    branches: list[dict[str, Any]],
    common_job_parameters: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    Sync every compute endpoint in the project in scope and return them, so the
    database sync can resolve each branch's connection hostname.
    """
    project_id = common_job_parameters["PROJECT_ID"]
    endpoints = get(api_session, common_job_parameters["BASE_URL"], project_id)
    load_endpoints(
        neo4j_session,
        transform_endpoints(endpoints, project, branches),
        project_id,
        common_job_parameters["UPDATE_TAG"],
    )
    GraphJob.from_node_schema(NeonEndpointSchema(), common_job_parameters).run(
        neo4j_session,
    )
    return endpoints


@timeit
def get(
    api_session: requests.Session,
    base_url: str,
    project_id: str,
) -> list[dict[str, Any]]:
    return get_json(api_session, f"{base_url}/projects/{project_id}/endpoints")[
        "endpoints"
    ]


def endpoint_exposure(
    endpoint: dict[str, Any],
    project: dict[str, Any],
    branch_protected: bool,
) -> dict[str, Any]:
    """
    Whether any internet address may open a connection to this compute.

    Neon applies the project's IP allowlist at the proxy in front of every
    compute. The compute is reachable from anywhere unless one of these holds:

    - the project blocks public connections, leaving only private networking;
    - the compute is disabled, so it refuses every connection;
    - the allowlist has entries and applies to this branch. With
      ``protected_branches_only`` it applies to protected branches only, so an
      unprotected branch (typically a preview branch cut from production data)
      stays open even though the project looks locked down.

    An allowlist entry that admits every address (``0.0.0.0/0``, ``::/0``) is
    the same as no allowlist.
    """
    settings = project.get("settings") or {}
    allowed_ips = settings.get("allowed_ips") or {}
    ips = allowed_ips.get("ips") or []
    protected_only = bool(allowed_ips.get("protected_branches_only"))

    if settings.get("block_public_connections") or endpoint.get("disabled"):
        exposed = False
    else:
        allowlist_applies = bool(ips) and (not protected_only or branch_protected)
        exposed = not allowlist_applies or any(ip in _ANY_ADDRESS for ip in ips)
    return {
        "exposed_internet": exposed,
        "exposed_internet_type": ["direct"] if exposed else None,
    }


def transform_endpoints(
    endpoints: list[dict[str, Any]],
    project: dict[str, Any],
    branches: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    protected_by_branch = {b["id"]: bool(b.get("protected")) for b in branches}
    result: list[dict[str, Any]] = []
    for endpoint in endpoints:
        hosts = endpoint.get("hosts") or {}
        result.append(
            {
                "id": endpoint["id"],
                "name": endpoint.get("name"),
                "host": endpoint["host"],
                "pooled_host": hosts.get("read_write_pooled_host")
                or hosts.get("read_only_pooled_host"),
                "branch_id": endpoint["branch_id"],
                "region_id": endpoint.get("region_id"),
                "type": endpoint.get("type"),
                "current_state": endpoint.get("current_state"),
                "disabled": endpoint.get("disabled"),
                "passwordless_access": endpoint.get("passwordless_access"),
                "pooler_enabled": endpoint.get("pooler_enabled"),
                "pooler_mode": endpoint.get("pooler_mode"),
                "autoscaling_limit_min_cu": endpoint.get("autoscaling_limit_min_cu"),
                "autoscaling_limit_max_cu": endpoint.get("autoscaling_limit_max_cu"),
                "suspend_timeout_seconds": endpoint.get("suspend_timeout_seconds"),
                "compute_release_version": endpoint.get("compute_release_version"),
                "creation_source": endpoint.get("creation_source"),
                "last_active": iso_to_datetime(endpoint.get("last_active")),
                "created_at": iso_to_datetime(endpoint.get("created_at")),
                "updated_at": iso_to_datetime(endpoint.get("updated_at")),
                **endpoint_exposure(
                    endpoint,
                    project,
                    protected_by_branch.get(endpoint["branch_id"], False),
                ),
            },
        )
    return result


@timeit
def load_endpoints(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    project_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        NeonEndpointSchema(),
        data,
        lastupdated=update_tag,
        PROJECT_ID=project_id,
    )
