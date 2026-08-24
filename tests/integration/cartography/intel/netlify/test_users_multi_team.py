"""
A Netlify user is a shared identity: the same person can belong to several teams.

One cartography run syncs exactly one team (`--netlify-account-slug` is required), so
a multi-team estate means several runs, each with its own update tag. That is the case these
tests pin down: syncing team A must never damage what team B's sync established for the same
person, and removing someone from team A must not delete them outright.
"""

from unittest.mock import MagicMock
from unittest.mock import patch

import neo4j
import requests

import cartography.intel.netlify.deploykeys
import cartography.intel.netlify.users
import tests.data.netlify.deploykeys
import tests.data.netlify.sites
import tests.data.netlify.users
from tests.integration.cartography.intel.netlify.common import common_job_parameters
from tests.integration.cartography.intel.netlify.common import (
    create_test_netlify_account,
)
from tests.integration.cartography.intel.netlify.common import TEST_ACCOUNT_ID
from tests.integration.cartography.intel.netlify.common import TEST_BASE_URL
from tests.integration.cartography.intel.netlify.common import TEST_UPDATE_TAG
from tests.integration.cartography.intel.netlify.common import TEST_USER_ID
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

_TEAM_A = TEST_ACCOUNT_ID
_TEAM_A_SLUG = "example-team"
_TEAM_B = "5f5a5d7053c60b4be4c8790f"
_TEAM_B_SLUG = "other-team"

# Netlify issues a separate membership row per team for the same person.
_MEMBER_IN_A = tests.data.netlify.users.NETLIFY_MEMBERS
# Deploy keys are only ingested for the team whose sites reference them, so a fixture site that
# does reference the key is what puts it in scope for both teams here.
_SITES_USING_THE_KEY = tests.data.netlify.sites.NETLIFY_SITES_WITH_GIT

_MEMBER_IN_B = [
    {
        **tests.data.netlify.users.NETLIFY_MEMBERS[0],
        "id": "5f5a5d7053c60b4be4c8791e",
        "role": "Collaborator",
        "site_access": "none",
    },
]


def _sync_team(
    neo4j_session: neo4j.Session,
    account_id: str,
    account_slug: str,
    members: list,
    update_tag: int,
) -> None:
    create_test_netlify_account(neo4j_session, account_id, update_tag)
    with patch.object(
        cartography.intel.netlify.users,
        "get_netlify_users",
        return_value=members,
    ):
        cartography.intel.netlify.users.sync_netlify_users(
            neo4j_session,
            MagicMock(spec=requests.Session),
            TEST_BASE_URL,
            account_id,
            account_slug,
            update_tag,
            common_job_parameters(account_id, update_tag),
        )


def test_syncing_one_team_keeps_another_teams_membership(
    neo4j_session: neo4j.Session,
) -> None:
    """
    Team B's sync runs after team A's, with a later update tag. A's edges are older but still
    valid, so nothing may remove them.
    """
    # Arrange / Act
    _sync_team(neo4j_session, _TEAM_A, _TEAM_A_SLUG, _MEMBER_IN_A, TEST_UPDATE_TAG)
    _sync_team(neo4j_session, _TEAM_B, _TEAM_B_SLUG, _MEMBER_IN_B, TEST_UPDATE_TAG + 1)

    # Assert: one node for the person, attached to both teams
    assert check_nodes(neo4j_session, "NetlifyUser", ["id"]) == {(TEST_USER_ID,)}
    assert check_rels(
        neo4j_session,
        "NetlifyAccount",
        "id",
        "NetlifyUser",
        "id",
        "RESOURCE",
    ) == {(_TEAM_A, TEST_USER_ID), (_TEAM_B, TEST_USER_ID)}
    assert check_rels(
        neo4j_session,
        "NetlifyUser",
        "id",
        "NetlifyAccount",
        "id",
        "MEMBER_OF",
    ) == {(TEST_USER_ID, _TEAM_A), (TEST_USER_ID, _TEAM_B)}


def test_removing_a_user_from_one_team_keeps_them_in_the_other(
    neo4j_session: neo4j.Session,
) -> None:
    """
    The regression this guards: the person leaves team A but is still in team B. Team A's
    cleanup must drop only A's two edges, not the node, and must not touch B's edges.
    """
    # Arrange: the person is in both teams
    _sync_team(neo4j_session, _TEAM_A, _TEAM_A_SLUG, _MEMBER_IN_A, TEST_UPDATE_TAG)
    _sync_team(neo4j_session, _TEAM_B, _TEAM_B_SLUG, _MEMBER_IN_B, TEST_UPDATE_TAG + 1)

    # Act: team A syncs again, without them
    _sync_team(neo4j_session, _TEAM_A, _TEAM_A_SLUG, [], TEST_UPDATE_TAG + 2)

    # Assert: still one node, still a member of B, no longer attached to A
    assert check_nodes(neo4j_session, "NetlifyUser", ["id"]) == {(TEST_USER_ID,)}
    assert check_rels(
        neo4j_session,
        "NetlifyAccount",
        "id",
        "NetlifyUser",
        "id",
        "RESOURCE",
    ) == {(_TEAM_B, TEST_USER_ID)}
    assert check_rels(
        neo4j_session,
        "NetlifyUser",
        "id",
        "NetlifyAccount",
        "id",
        "MEMBER_OF",
    ) == {(TEST_USER_ID, _TEAM_B)}


def test_removing_a_user_from_their_last_team_leaves_no_membership(
    neo4j_session: neo4j.Session,
) -> None:
    """
    A shared identity node is deliberately never deleted by a team's cleanup: other teams, and
    other modules, may still reference it. What must go is every membership edge, so the person
    stops showing up as belonging to the team.
    """
    # Arrange
    _sync_team(neo4j_session, _TEAM_A, _TEAM_A_SLUG, _MEMBER_IN_A, TEST_UPDATE_TAG)

    # Act
    _sync_team(neo4j_session, _TEAM_A, _TEAM_A_SLUG, [], TEST_UPDATE_TAG + 1)

    # Assert. Scoped to team A rather than asserting the graph is empty: neo4j_session is
    # module-scoped, so edges another test in this file created still exist.
    edges = neo4j_session.run(
        """
        MATCH (u:NetlifyUser)-[r]-(a:NetlifyAccount{id: $account_id})
        RETURN type(r) AS rel_type
        """,
        account_id=_TEAM_A,
    ).values()
    assert edges == []

    # The identity itself survives: deleting it would be the very regression this file guards.
    assert check_nodes(neo4j_session, "NetlifyUser", ["id"]) == {(TEST_USER_ID,)}


def test_syncing_one_team_keeps_another_teams_deploy_keys(
    neo4j_session: neo4j.Session,
) -> None:
    """
    `GET /deploy_keys` takes no team parameter, so both teams' syncs see the same keys and stamp
    the node with their own tag. Team A's cleanup must not delete a key team B just refreshed.
    """
    # Arrange
    keys = tests.data.netlify.deploykeys.NETLIFY_DEPLOY_KEYS
    key_id = keys[0]["id"]

    def sync_keys(account_id: str, update_tag: int) -> None:
        create_test_netlify_account(neo4j_session, account_id, update_tag)
        with patch.object(
            cartography.intel.netlify.deploykeys,
            "get_netlify_deploy_keys",
            return_value=keys,
        ):
            cartography.intel.netlify.deploykeys.sync_netlify_deploy_keys(
                neo4j_session,
                MagicMock(spec=requests.Session),
                TEST_BASE_URL,
                account_id,
                _SITES_USING_THE_KEY,
                update_tag,
                common_job_parameters(account_id, update_tag),
            )

    # Act: team A, then team B, then team A again
    sync_keys(_TEAM_A, TEST_UPDATE_TAG)
    sync_keys(_TEAM_B, TEST_UPDATE_TAG + 1)
    sync_keys(_TEAM_A, TEST_UPDATE_TAG + 2)

    # Assert: the key survived every pass and is still attached to both teams
    assert check_nodes(neo4j_session, "NetlifyDeployKey", ["id"]) == {(key_id,)}
    assert check_rels(
        neo4j_session,
        "NetlifyAccount",
        "id",
        "NetlifyDeployKey",
        "id",
        "RESOURCE",
    ) == {(_TEAM_A, key_id), (_TEAM_B, key_id)}


def test_membership_role_is_per_team(neo4j_session: neo4j.Session) -> None:
    """
    The same person holds a different role in each team, so the role has to live on the edge.
    Writing it to the node would have team B's sync overwrite team A's value.
    """
    # Arrange / Act
    _sync_team(neo4j_session, _TEAM_A, _TEAM_A_SLUG, _MEMBER_IN_A, TEST_UPDATE_TAG)
    _sync_team(neo4j_session, _TEAM_B, _TEAM_B_SLUG, _MEMBER_IN_B, TEST_UPDATE_TAG + 1)

    # Assert
    roles = {
        (record["account_id"], record["role"], record["site_access"])
        for record in neo4j_session.run(
            """
            MATCH (:NetlifyUser)-[r:MEMBER_OF]->(a:NetlifyAccount)
            RETURN a.id AS account_id, r.role AS role, r.site_access AS site_access
            """,
        )
    }
    assert roles == {
        (_TEAM_A, "Owner", "all"),
        (_TEAM_B, "Collaborator", "none"),
    }
