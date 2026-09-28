import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.netlify.util import get_list
from cartography.models.netlify.buildhook import NetlifyBuildHookSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync_netlify_build_hooks(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    base_url: str,
    account_id: str,
    sites: list[dict[str, Any]],
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    raw_hooks = []
    for site in sites:
        raw_hooks.extend(get_netlify_build_hooks(api_session, base_url, site["id"]))
    hooks = transform_netlify_build_hooks(raw_hooks)
    load_netlify_build_hooks(neo4j_session, hooks, account_id, update_tag)
    cleanup_netlify_build_hooks(neo4j_session, common_job_parameters)


@timeit
def get_netlify_build_hooks(
    api_session: requests.Session,
    base_url: str,
    site_id: str,
) -> list[dict[str, Any]]:
    return get_list(api_session, f"{base_url}/sites/{site_id}/build_hooks")


def transform_netlify_build_hooks(
    hooks: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Strip the trigger URL and the message that repeats it.

    `url` deploys the site to anyone who holds it, and `msg` is a human-readable sentence with
    the same URL embedded, so both have to go.
    """
    return [
        {k: v for k, v in hook.items() if k not in ("url", "msg")} for hook in hooks
    ]


@timeit
def load_netlify_build_hooks(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        NetlifyBuildHookSchema(),
        data,
        lastupdated=update_tag,
        NETLIFY_ACCOUNT_ID=account_id,
    )


@timeit
def cleanup_netlify_build_hooks(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(NetlifyBuildHookSchema(), common_job_parameters).run(
        neo4j_session,
    )
