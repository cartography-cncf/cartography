import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.netlify.util import paginated_get
from cartography.models.netlify.hook import NetlifyHookSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync_netlify_hooks(
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
        raw_hooks.extend(get_netlify_hooks(api_session, base_url, site["id"]))
    hooks = transform_netlify_hooks(raw_hooks)
    load_netlify_hooks(neo4j_session, hooks, account_id, update_tag)
    cleanup_netlify_hooks(neo4j_session, common_job_parameters)


@timeit
def get_netlify_hooks(
    api_session: requests.Session,
    base_url: str,
    site_id: str,
) -> list[dict[str, Any]]:
    return paginated_get(
        api_session,
        f"{base_url}/hooks",
        params={"site_id": site_id},
    )


def transform_netlify_hooks(hooks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Strip the destination payload.

    `data` holds whatever the hook type needs to reach its destination: a Slack incoming-webhook
    URL, a target webhook URL, an email address, or a git provider access token. All of it is
    either a credential or personal data, so none of it is ingested.
    """
    return [{k: v for k, v in hook.items() if k != "data"} for hook in hooks]


@timeit
def load_netlify_hooks(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        NetlifyHookSchema(),
        data,
        lastupdated=update_tag,
        NETLIFY_ACCOUNT_ID=account_id,
    )


@timeit
def cleanup_netlify_hooks(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(NetlifyHookSchema(), common_job_parameters).run(
        neo4j_session,
    )
