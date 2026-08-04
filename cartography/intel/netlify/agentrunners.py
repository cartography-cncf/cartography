import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.netlify.util import paginated_get
from cartography.models.netlify.agentrunner import NetlifyAgentRunnerSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync_netlify_agent_runners(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    base_url: str,
    account_id: str,
    sites: list[dict[str, Any]],
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    raw_runners = []
    for site in sites:
        raw_runners.extend(
            get_netlify_agent_runners(api_session, base_url, account_id, site["id"]),
        )
    runners = transform_netlify_agent_runners(raw_runners)
    load_netlify_agent_runners(neo4j_session, runners, account_id, update_tag)
    cleanup_netlify_agent_runners(neo4j_session, common_job_parameters)


@timeit
def get_netlify_agent_runners(
    api_session: requests.Session,
    base_url: str,
    account_id: str,
    site_id: str,
) -> list[dict[str, Any]]:
    """
    Fetch the agent runners of one site.

    The endpoint requires both `account_id` and `site_id`, so there is no way to enumerate a
    whole team in one call.
    """
    return paginated_get(
        api_session,
        f"{base_url}/agent_runners",
        params={"account_id": account_id, "site_id": site_id},
    )


def transform_netlify_agent_runners(
    runners: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Flatten the nested creator object.

    The `contributors` array is dropped: it repeats the creator plus anyone who has looked at
    the runner, which is session activity rather than inventory.
    """
    transformed = []
    for runner in runners:
        user = runner.get("user") or {}
        transformed.append(
            {
                **{
                    k: v for k, v in runner.items() if k not in ("user", "contributors")
                },
                "user_id": user.get("id"),
            },
        )
    return transformed


@timeit
def load_netlify_agent_runners(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        NetlifyAgentRunnerSchema(),
        data,
        lastupdated=update_tag,
        NETLIFY_ACCOUNT_ID=account_id,
    )


@timeit
def cleanup_netlify_agent_runners(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(NetlifyAgentRunnerSchema(), common_job_parameters).run(
        neo4j_session,
    )
