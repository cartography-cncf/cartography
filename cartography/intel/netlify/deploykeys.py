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
    sites: list[dict[str, Any]],
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Sync the deploy keys this team's sites actually clone with.

    Must run before the sites are loaded: the site's `USES_DEPLOY_KEY` edge is resolved by a MATCH
    at site-load time, so a key node that does not exist yet produces no edge at all until the
    next sync. It takes the site list rather than fetching one, because the entry point already
    has it and needs it here to decide which keys belong to this team.
    """
    raw_keys = get_netlify_deploy_keys(api_session, base_url)
    deploy_keys = transform_netlify_deploy_keys(raw_keys, account_id, sites)
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
    sites: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Keep only the keys a site in this team clones with, and carry the team id for the MatchLink.

    `GET /deploy_keys` has no team filter, so it returns every key the token can see. Attributing
    all of them to the team being synced would give a multi-team token a RESOURCE edge from every
    team to every key, which says nothing. A site's `build_settings.deploy_key_id` is the only
    statement of ownership the API makes, so that is what decides membership here.

    A key no site references is therefore not ingested. It cannot be attributed to a team, and an
    unreferenced key is arguably worth surfacing on its own, but doing that needs a scope this
    module does not have: the token's, not the team's.
    """
    referenced = {
        (site.get("build_settings") or {}).get("deploy_key_id") for site in sites
    }
    referenced.discard(None)
    return [
        {**key, "account_id": account_id}
        for key in deploy_keys
        if key["id"] in referenced
    ]


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
