import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.client.core.tx import load_matchlinks
from cartography.graph.job import GraphJob
from cartography.intel.netlify.util import get_list
from cartography.models.netlify.deploykey import NetlifyDeployKeySchema
from cartography.models.netlify.deploykey import NetlifyDeployKeyToAccountMatchLink
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync_netlify_deploy_keys(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    base_url: str,
    account_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    raw_keys = get_netlify_deploy_keys(api_session, base_url)
    deploy_keys = transform_netlify_deploy_keys(raw_keys, account_id)
    load_netlify_deploy_keys(neo4j_session, deploy_keys, account_id, update_tag)
    cleanup_netlify_deploy_keys(neo4j_session, account_id, update_tag)


@timeit
def get_netlify_deploy_keys(
    api_session: requests.Session,
    base_url: str,
) -> list[dict[str, Any]]:
    """
    Fetch every deploy key the token can see.

    The endpoint takes no team parameter, so the result is scoped to the token rather than to the
    team being synced. That is why the team edge is a MatchLink; see the model's docstring.
    """
    return get_list(api_session, f"{base_url}/deploy_keys")


def transform_netlify_deploy_keys(
    deploy_keys: list[dict[str, Any]],
    account_id: str,
) -> list[dict[str, Any]]:
    """Carry the team id for the MatchLink, which has no kwargs to read it from."""
    return [{**key, "account_id": account_id} for key in deploy_keys]


@timeit
def load_netlify_deploy_keys(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        NetlifyDeployKeySchema(),
        data,
        lastupdated=update_tag,
    )
    load_matchlinks(
        neo4j_session,
        NetlifyDeployKeyToAccountMatchLink(),
        data,
        lastupdated=update_tag,
        _sub_resource_label="NetlifyAccount",
        _sub_resource_id=account_id,
    )


@timeit
def cleanup_netlify_deploy_keys(
    neo4j_session: neo4j.Session,
    account_id: str,
    update_tag: int,
) -> None:
    # Only this team's edge is cleaned up. The key node is not deleted here: the endpoint is
    # token-scoped, so another team's sync may legitimately have refreshed it more recently.
    GraphJob.from_matchlink(
        NetlifyDeployKeyToAccountMatchLink(),
        "NetlifyAccount",
        account_id,
        update_tag,
    ).run(neo4j_session)
