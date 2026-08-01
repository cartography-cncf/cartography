from unittest.mock import MagicMock
from unittest.mock import patch

import neo4j
import requests

import cartography.intel.netlify.users
import tests.data.netlify.users
from tests.integration.cartography.intel.netlify.common import common_job_parameters
from tests.integration.cartography.intel.netlify.common import (
    create_test_netlify_account,
)
from tests.integration.cartography.intel.netlify.common import TEST_ACCOUNT_ID
from tests.integration.cartography.intel.netlify.common import TEST_ACCOUNT_SLUG
from tests.integration.cartography.intel.netlify.common import TEST_BASE_URL
from tests.integration.cartography.intel.netlify.common import TEST_UPDATE_TAG
from tests.integration.cartography.intel.netlify.common import TEST_USER_ID
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

_MEMBERSHIP_ID = "5f5a5d7053c60b4be4c8784e"
_OTHER_ACCOUNT_ID = "5f5a5d7053c60b4be4c87850"


@patch.object(
    cartography.intel.netlify.users,
    "get_netlify_users",
    return_value=tests.data.netlify.users.NETLIFY_MEMBERS,
)
def test_sync_netlify_users(mock_get, neo4j_session: neo4j.Session) -> None:
    # Arrange
    create_test_netlify_account(neo4j_session)
    api_session = MagicMock(spec=requests.Session)

    # Act
    cartography.intel.netlify.users.sync_netlify_users(
        neo4j_session,
        api_session,
        TEST_BASE_URL,
        TEST_ACCOUNT_ID,
        TEST_ACCOUNT_SLUG,
        TEST_UPDATE_TAG,
        common_job_parameters(),
    )

    # Assert Nodes: keyed on the person's user_id, not the membership id, and carrying only
    # identity-level facts. Anything team-scoped is on the edge, asserted below.
    assert check_nodes(
        neo4j_session,
        "NetlifyUser",
        ["id", "email", "full_name", "mfa_enabled", "last_activity_date"],
    ) == {(TEST_USER_ID, "alice@example.com", "Alice Example", False, "2026-07-30")}

    # Membership-scoped fields must not be on the shared node: whichever team synced last would
    # otherwise decide their value for everyone.
    assert check_nodes(
        neo4j_session,
        "NetlifyUser",
        ["pending", "role", "site_access", "managed_by_directory_sync", "created_at"],
    ) == {(None, None, None, None, None)}

    # Assert the linked-identity map was flattened to a scalar array. Queried directly rather
    # than through check_nodes(), which builds a set of tuples and so cannot hold a list.
    assert neo4j_session.run(
        "MATCH (u:NetlifyUser) RETURN u.connected_account_providers AS providers",
    ).single()["providers"] == ["google"]

    # Assert Relationships
    assert check_rels(
        neo4j_session,
        "NetlifyAccount",
        "id",
        "NetlifyUser",
        "id",
        "RESOURCE",
    ) == {(TEST_ACCOUNT_ID, TEST_USER_ID)}
    assert check_rels(
        neo4j_session,
        "NetlifyUser",
        "id",
        "NetlifyAccount",
        "id",
        "MEMBER_OF",
    ) == {(TEST_USER_ID, TEST_ACCOUNT_ID)}

    # Assert the per-team facts live on the MEMBER_OF edge, not the node
    membership = neo4j_session.run(
        """
        MATCH (:NetlifyUser)-[r:MEMBER_OF]->(:NetlifyAccount)
        RETURN r.role AS role, r.site_access AS site_access,
               r.membership_id AS membership_id, r.pending AS pending,
               r.managed_by_directory_sync AS managed_by_directory_sync,
               r.created_at AS created_at
        """,
    ).single()
    assert membership["role"] == "Owner"
    assert membership["site_access"] == "all"
    assert membership["membership_id"] == _MEMBERSHIP_ID
    assert membership["pending"] is False
    assert membership["managed_by_directory_sync"] is False
    assert membership["created_at"] == "2026-07-30T15:32:17.370Z"

    # Assert the ontology label and its projected properties. `active` is deliberately absent:
    # Netlify's only signal is the membership-scoped `pending`, which cannot be projected onto a
    # shared identity without one team overwriting another.
    assert check_nodes(
        neo4j_session,
        "UserAccount",
        ["id", "_ont_email", "_ont_has_mfa", "_ont_active", "_ont_source"],
    ) == {(TEST_USER_ID, "alice@example.com", False, None, "netlify")}


def test_an_unaccepted_invitation_becomes_its_own_node(
    neo4j_session: neo4j.Session,
) -> None:
    """
    An invited address has no `user_id`, and NetlifyUser is keyed on it, so those rows would make
    the whole batch fail on a null merge key. They become NetlifyInvite nodes keyed on the email.
    """
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    create_test_netlify_account(neo4j_session)
    members = [
        {
            "id": "invite-row-1",
            "user_id": None,
            "email": "invited@example.com",
            "pending": True,
            "role": "Collaborator",
            "site_access": "none",
        },
        tests.data.netlify.users.NETLIFY_MEMBERS[0],
    ]

    # Act
    with patch.object(
        cartography.intel.netlify.users,
        "get_netlify_users",
        return_value=members,
    ):
        cartography.intel.netlify.users.sync_netlify_users(
            neo4j_session,
            MagicMock(spec=requests.Session),
            TEST_BASE_URL,
            TEST_ACCOUNT_ID,
            TEST_ACCOUNT_SLUG,
            TEST_UPDATE_TAG,
            common_job_parameters(),
        )

    # Assert: the person and the invitation are separate nodes, neither with a null id
    assert check_nodes(neo4j_session, "NetlifyUser", ["id"]) == {(TEST_USER_ID,)}
    assert check_nodes(neo4j_session, "NetlifyInvite", ["id", "email"]) == {
        ("invited@example.com", "invited@example.com"),
    }

    # Assert Relationships: INVITED_TO rather than MEMBER_OF, with the pending role on the edge
    assert check_rels(
        neo4j_session,
        "NetlifyInvite",
        "id",
        "NetlifyAccount",
        "id",
        "INVITED_TO",
    ) == {("invited@example.com", TEST_ACCOUNT_ID)}
    assert check_rels(
        neo4j_session,
        "NetlifyUser",
        "id",
        "NetlifyAccount",
        "id",
        "MEMBER_OF",
    ) == {(TEST_USER_ID, TEST_ACCOUNT_ID)}
    invitation = neo4j_session.run(
        """
        MATCH (:NetlifyInvite)-[r:INVITED_TO]->(:NetlifyAccount)
        RETURN r.role AS role, r.membership_id AS membership_id
        """,
    ).single()
    assert invitation["role"] == "Collaborator"
    assert invitation["membership_id"] == "invite-row-1"


def test_an_invitation_that_ended_is_deleted_unless_another_team_still_holds_it(
    neo4j_session: neo4j.Session,
) -> None:
    """
    An accepted or revoked invitation leaves the members list, so the edge cleanup drops its
    INVITED_TO and the node has nothing left to stand for. It must go, or the person it named
    lingers forever alongside the NetlifyUser they became. An address still invited to a second
    team keeps its other INVITED_TO and so must survive this team's sync.
    """
    # Arrange: two addresses invited to this team, one of them also invited to a second team
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    create_test_netlify_account(neo4j_session)
    create_test_netlify_account(neo4j_session, account_id=_OTHER_ACCOUNT_ID)
    invited_twice = {
        "id": "invite-row-1",
        "user_id": None,
        "email": "invited-twice@example.com",
        "pending": True,
        "role": "Collaborator",
    }
    ending = {
        "id": "invite-row-2",
        "user_id": None,
        "email": "ending@example.com",
        "pending": True,
        "role": "Collaborator",
    }
    for account_id, members in (
        (TEST_ACCOUNT_ID, [invited_twice, ending]),
        (_OTHER_ACCOUNT_ID, [invited_twice]),
    ):
        _, invites = cartography.intel.netlify.users.transform_netlify_users(
            members,
            account_id,
        )
        cartography.intel.netlify.users.load_netlify_invites(
            neo4j_session,
            invites,
            account_id,
            TEST_UPDATE_TAG,
        )
    assert check_nodes(neo4j_session, "NetlifyInvite", ["id"]) == {
        ("invited-twice@example.com",),
        ("ending@example.com",),
    }

    # Act: re-sync only this team, with the second invitation gone from the members list
    with patch.object(
        cartography.intel.netlify.users,
        "get_netlify_users",
        return_value=[invited_twice],
    ):
        cartography.intel.netlify.users.sync_netlify_users(
            neo4j_session,
            MagicMock(spec=requests.Session),
            TEST_BASE_URL,
            TEST_ACCOUNT_ID,
            TEST_ACCOUNT_SLUG,
            TEST_UPDATE_TAG + 1,
            common_job_parameters(update_tag=TEST_UPDATE_TAG + 1),
        )

    # Assert: the ended invitation is gone, the one the other team still holds is not
    assert check_nodes(neo4j_session, "NetlifyInvite", ["id"]) == {
        ("invited-twice@example.com",),
    }
    assert check_rels(
        neo4j_session,
        "NetlifyInvite",
        "id",
        "NetlifyAccount",
        "id",
        "INVITED_TO",
    ) == {
        ("invited-twice@example.com", TEST_ACCOUNT_ID),
        ("invited-twice@example.com", _OTHER_ACCOUNT_ID),
    }


def test_an_existing_user_invited_to_a_team_stays_a_user(
    neo4j_session: neo4j.Session,
) -> None:
    """
    Someone who already has a Netlify account and is invited to a further team arrives with
    `user_id` set and `pending` true. Splitting on `pending` would turn that person into an Invite
    and lose their identity; the split is on `user_id` precisely so this stays a NetlifyUser with a
    pending MEMBER_OF.
    """
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    create_test_netlify_account(neo4j_session)
    members = [
        {
            **tests.data.netlify.users.NETLIFY_MEMBERS[0],
            "pending": True,
            "invite_id": "invite-abc",
        },
    ]

    # Act
    with patch.object(
        cartography.intel.netlify.users,
        "get_netlify_users",
        return_value=members,
    ):
        cartography.intel.netlify.users.sync_netlify_users(
            neo4j_session,
            MagicMock(spec=requests.Session),
            TEST_BASE_URL,
            TEST_ACCOUNT_ID,
            TEST_ACCOUNT_SLUG,
            TEST_UPDATE_TAG,
            common_job_parameters(),
        )

    # Assert: a user, not an invite, and the pending state is on the edge
    assert check_nodes(neo4j_session, "NetlifyUser", ["id"]) == {(TEST_USER_ID,)}
    assert check_nodes(neo4j_session, "NetlifyInvite", ["id"]) == set()
    membership = neo4j_session.run(
        """
        MATCH (:NetlifyUser)-[r:MEMBER_OF]->(:NetlifyAccount)
        RETURN r.pending AS pending, r.invite_id AS invite_id
        """,
    ).single()
    assert membership["pending"] is True
    assert membership["invite_id"] == "invite-abc"
