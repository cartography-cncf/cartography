import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.netlify.util import paginated_get
from cartography.models.netlify.devserver import NetlifyDevServerSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync_netlify_dev_servers(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    base_url: str,
    account_id: str,
    sites: list[dict[str, Any]],
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    dev_servers = []
    for site in sites:
        dev_servers.extend(
            get_netlify_dev_servers(api_session, base_url, site["id"]),
        )
    load_netlify_dev_servers(neo4j_session, dev_servers, account_id, update_tag)
    cleanup_netlify_dev_servers(neo4j_session, common_job_parameters)


@timeit
def get_netlify_dev_servers(
    api_session: requests.Session,
    base_url: str,
    site_id: str,
) -> list[dict[str, Any]]:
    return paginated_get(
        api_session,
        f"{base_url}/sites/{site_id}/dev_servers",
    )


@timeit
def load_netlify_dev_servers(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        NetlifyDevServerSchema(),
        data,
        lastupdated=update_tag,
        NETLIFY_ACCOUNT_ID=account_id,
    )


@timeit
def cleanup_netlify_dev_servers(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(NetlifyDevServerSchema(), common_job_parameters).run(
        neo4j_session,
    )
