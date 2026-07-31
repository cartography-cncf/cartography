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

    Members with no `user_id` are skipped. `POST /{account_slug}/members` takes only a role and an
    email address, so a membership exists before any Netlify user is attached to it, and the row
    for an unaccepted invitation has no person to key a node on. That matters because the node id
    is `user_id`: a null one does not merely drop its own row, it aborts the whole batch with
    `Cannot merge the following node because of null property value for 'id'`, so a single pending
    invitation would take the team's entire user sync with it.

    Skipping loses the fact that an address has been invited. Representing those rows separately,
    keyed on `membership_id`, would keep it, but it needs the real payload of a pending invitation
    to model correctly and that has not been observed yet.
    """
    transformed = []
    skipped = 0
    for member in members:
        if not member.get("user_id"):
            skipped += 1
            continue
        connected_accounts = member.get("connected_accounts") or {}
        transformed.append(
            {
                **{k: v for k, v in member.items() if k != "id"},
                "membership_id": member["id"],
                "account_id": account_id,
                "connected_account_providers": sorted(connected_accounts.keys()),
            },
        )
    if skipped:
        logger.warning(
            "Skipped %d Netlify membership(s) with no user_id, most likely unaccepted "
            "invitations. They are not represented in the graph.",
            skipped,
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
