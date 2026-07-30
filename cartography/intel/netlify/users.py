import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.client.core.tx import load_matchlinks
from cartography.graph.job import GraphJob
from cartography.intel.netlify.util import paginated_get
from cartography.models.netlify.user import NetlifyUserMemberOfAccountMatchLink
from cartography.models.netlify.user import NetlifyUserSchema
from cartography.models.netlify.user import NetlifyUserToAccountMatchLink
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
    transformed = transform_netlify_users(members, account_id)
    load_netlify_users(neo4j_session, transformed, account_id, update_tag)
    cleanup_netlify_users(neo4j_session, account_id, update_tag)


@timeit
def get_netlify_users(
    api_session: requests.Session,
    base_url: str,
    account_slug: str,
) -> list[dict[str, Any]]:
    return paginated_get(api_session, f"{base_url}/{account_slug}/members")


def transform_netlify_users(
    members: list[dict[str, Any]],
    account_id: str,
) -> list[dict[str, Any]]:
    """
    Flatten the linked-identity map and carry the team id for the membership MatchLinks.

    Netlify returns `connected_accounts` as a provider-keyed map, e.g.
    ``{"google": "user@example.com"}``. The email is already on the node, so only the provider
    names are kept.

    Netlify's `id` is the membership row, not the person, so it is renamed to `membership_id`:
    it belongs on the MEMBER_OF edge, and leaving it under `id` invites a future model to key the
    node on it.
    """
    transformed = []
    for member in members:
        connected_accounts = member.get("connected_accounts") or {}
        transformed.append(
            {
                **{k: v for k, v in member.items() if k != "id"},
                "membership_id": member["id"],
                "account_id": account_id,
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
    # The node carries no team scoping: it is a shared identity keyed on the person.
    load(
        neo4j_session,
        NetlifyUserSchema(),
        data,
        lastupdated=update_tag,
    )
    # Both team edges are MatchLinks so their cleanup is scoped to the team being synced. As
    # node-schema relationships, the MEMBER_OF cleanup would match every team's edges at once and
    # the node cleanup would DETACH DELETE anyone whose other team stamped a different tag.
    for matchlink in (
        NetlifyUserToAccountMatchLink(),
        NetlifyUserMemberOfAccountMatchLink(),
    ):
        load_matchlinks(
            neo4j_session,
            matchlink,
            data,
            lastupdated=update_tag,
            _sub_resource_label="NetlifyAccount",
            _sub_resource_id=account_id,
        )


@timeit
def cleanup_netlify_users(
    neo4j_session: neo4j.Session,
    account_id: str,
    update_tag: int,
) -> None:
    # Only the edges are cleaned up, and only this team's. The NetlifyUser node is never deleted
    # here: other teams and other modules may still reference the identity. A person removed from
    # their last team keeps a bare node with no membership, which is the same outcome Railway and
    # GitHub produce for a shared principal.
    for matchlink in (
        NetlifyUserMemberOfAccountMatchLink(),
        NetlifyUserToAccountMatchLink(),
    ):
        GraphJob.from_matchlink(
            matchlink,
            "NetlifyAccount",
            account_id,
            update_tag,
        ).run(neo4j_session)
