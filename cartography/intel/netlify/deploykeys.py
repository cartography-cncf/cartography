import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.netlify.util import get_list
from cartography.models.netlify.deploykey import NetlifyDeployKeySchema
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
    deploy_keys = get_netlify_deploy_keys(api_session, base_url)
    load_netlify_deploy_keys(neo4j_session, deploy_keys, account_id, update_tag)
    cleanup_netlify_deploy_keys(neo4j_session, common_job_parameters)


@timeit
def get_netlify_deploy_keys(
    api_session: requests.Session,
    base_url: str,
) -> list[dict[str, Any]]:
    """
    Fetch every deploy key the token can see.

    The endpoint is account-wide rather than per-site: a key can be shared by several sites, and
    the site is the side that records which key it uses.
    """
    return get_list(api_session, f"{base_url}/deploy_keys")


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
        NETLIFY_ACCOUNT_ID=account_id,
    )


@timeit
def cleanup_netlify_deploy_keys(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(NetlifyDeployKeySchema(), common_job_parameters).run(
        neo4j_session,
    )
