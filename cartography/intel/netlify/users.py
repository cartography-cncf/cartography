import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.netlify.util import paginated_get
from cartography.models.netlify.user import NetlifyUserSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync_netlify_users(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    base_url: str,
    account_id: str,
    account_slug: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    members = get_netlify_users(api_session, base_url, account_slug)
    transformed = transform_netlify_users(members)
    load_netlify_users(neo4j_session, transformed, account_id, update_tag)
    cleanup_netlify_users(neo4j_session, common_job_parameters)


@timeit
def get_netlify_users(
    api_session: requests.Session,
    base_url: str,
    account_slug: str,
) -> list[dict[str, Any]]:
    return paginated_get(api_session, f"{base_url}/{account_slug}/members")


def transform_netlify_users(
    members: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Flatten the linked-identity map into a list Neo4j can store as a scalar array.

    Netlify returns `connected_accounts` as a provider-keyed map, e.g.
    ``{"google": "user@example.com"}``. The email is already on the node, so only the provider
    names are kept.
    """
    transformed = []
    for member in members:
        connected_accounts = member.get("connected_accounts") or {}
        transformed.append(
            {
                **member,
                "connected_account_providers": sorted(connected_accounts.keys()),
            },
        )
    return transformed


@timeit
def load_netlify_users(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        NetlifyUserSchema(),
        data,
        lastupdated=update_tag,
        NETLIFY_ACCOUNT_ID=account_id,
    )


@timeit
def cleanup_netlify_users(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(NetlifyUserSchema(), common_job_parameters).run(
        neo4j_session,
    )
