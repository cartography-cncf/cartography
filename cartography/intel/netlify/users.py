import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.client.core.tx import load_matchlinks
from cartography.graph.job import GraphJob
from cartography.intel.netlify.util import paginated_get
from cartography.models.netlify.invite import NetlifyInvitedToAccountMatchLink
from cartography.models.netlify.invite import NetlifyInviteSchema
from cartography.models.netlify.invite import NetlifyInviteToAccountMatchLink
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
    users, invites = transform_netlify_users(members, account_id)
    load_netlify_users(neo4j_session, users, account_id, update_tag)
    load_netlify_invites(neo4j_session, invites, account_id, update_tag)
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
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """
    Split the membership list into people and unaccepted invitations.

    An invited address has no `user_id` yet, and NetlifyUser is keyed on it, so those rows become
    NetlifyInvite nodes keyed on the email instead.

    :return: (members with a Netlify user, unaccepted invitations)
    """
    users: list[dict[str, Any]] = []
    invites: list[dict[str, Any]] = []
    for member in members:
        common = {
            **{k: v for k, v in member.items() if k != "id"},
            "membership_id": member["id"],
            "account_id": account_id,
        }
        if member.get("user_id"):
            connected_accounts = member.get("connected_accounts") or {}
            users.append(
                {
                    **common,
                    "connected_account_providers": sorted(connected_accounts.keys()),
                },
            )
            continue
        email = member.get("email")
        if not email:
            # Neither identity is available, so there is nothing to key a node on either way.
            logger.warning(
                "Skipping Netlify membership %s: it has neither a user_id nor an email.",
                member["id"],
            )
            continue
        invites.append(common)
    return users, invites


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
def load_netlify_invites(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    """
    Load unaccepted invitations, keyed on the invited email address.

    Same shape as the users above: the node carries no team scoping and both team edges are
    MatchLinks, because the same address can be invited to several teams.
    """
    load(
        neo4j_session,
        NetlifyInviteSchema(),
        data,
        lastupdated=update_tag,
    )
    for matchlink in (
        NetlifyInviteToAccountMatchLink(),
        NetlifyInvitedToAccountMatchLink(),
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
        NetlifyInvitedToAccountMatchLink(),
        NetlifyInviteToAccountMatchLink(),
    ):
        GraphJob.from_matchlink(
            matchlink,
            "NetlifyAccount",
            account_id,
            update_tag,
        ).run(neo4j_session)
