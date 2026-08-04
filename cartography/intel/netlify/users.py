import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.client.core.tx import load_matchlinks
from cartography.graph.job import GraphJob
from cartography.graph.statement import GraphStatement
from cartography.intel.netlify.util import paginated_get
from cartography.models.netlify.invite import NetlifyInvitedToAccountMatchLink
from cartography.models.netlify.invite import NetlifyInviteSchema
from cartography.models.netlify.invite import NetlifyInviteToAccountMatchLink
from cartography.models.netlify.user import NetlifyUserMemberOfAccountMatchLink
from cartography.models.netlify.user import NetlifyUserSchema
from cartography.models.netlify.user import NetlifyUserToAccountMatchLink
from cartography.util import timeit

logger = logging.getLogger(__name__)

ORPHANED_INVITE_CLEANUP_ITERATION_SIZE = 100


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
    Split the membership list by whether Netlify has linked a user to it.

    The split is on `user_id`, and deliberately not on `pending` or `invite_id`. Those describe the
    state of the membership, not whether a person exists: a Netlify user who already has an account
    and is invited to a second team arrives with `user_id` set and `pending` true, and must stay a
    NetlifyUser with a pending MEMBER_OF rather than becoming an Invite. `user_id` is what decides
    whether a NetlifyUser node can be keyed at all, so it is what decides the node type; `pending`
    and `invite_id` ride on the edge in both branches.

    A row with no `user_id` and no email cannot be keyed either way, so it is skipped.

    :return: (memberships with a linked Netlify user, memberships known only by email)
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
        if not member.get("email"):
            logger.warning(
                "Skipping Netlify membership %s: it has neither a user_id nor an email.",
                member["id"],
            )
            continue
        # A membership with no linked user is expected to be an outstanding invitation. If Netlify
        # says otherwise, the assumption behind this split is wrong and worth surfacing rather than
        # quietly modelling the row as an invite.
        if not member.get("pending") and not member.get("invite_id"):
            logger.warning(
                "Netlify membership %s has no user_id but is not marked pending and carries no "
                "invite_id. Treating it as an invitation keyed on %s; please report this payload.",
                member["id"],
                member["email"],
            )
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
    cleanup_netlify_orphaned_invites(neo4j_session)


@timeit
def cleanup_netlify_orphaned_invites(neo4j_session: neo4j.Session) -> None:
    """
    Delete invitations that are no longer outstanding anywhere.

    An invitation ends by being accepted or revoked, and either way the row leaves the members
    list, so the edge cleanup above drops its INVITED_TO. Unlike NetlifyUser, the node has no
    meaning once that happens: it stands for a pending invitation, not for a person, and an
    accepted one is now a NetlifyUser keyed on the real user_id. Left behind it would duplicate
    that person forever.

    The predicate is the absence of any remaining INVITED_TO rather than a stale lastupdated, so
    an address still invited to another team survives: that team's edge is untouched by this
    team's sync, and it keeps the node alive.
    """
    # Delete iteratively in chunks so a large backlog doesn't exhaust transaction memory.
    GraphStatement(
        """
        MATCH (i:NetlifyInvite)
        WHERE NOT (i)-[:INVITED_TO]->(:NetlifyAccount)
        WITH i LIMIT $LIMIT_SIZE
        DETACH DELETE i;
        """,
        iterative=True,
        iterationsize=ORPHANED_INVITE_CLEANUP_ITERATION_SIZE,
        parent_job_name="NetlifyInvite",
    ).run(neo4j_session)
