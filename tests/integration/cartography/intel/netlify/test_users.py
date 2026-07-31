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


def test_a_membership_with_no_user_id_does_not_abort_the_load(
    neo4j_session: neo4j.Session,
) -> None:
    """
    `POST /{account_slug}/members` takes only a role and an email, so a membership row exists
    before any Netlify user is attached to it. The node id is `user_id`, and a null one does not
    just drop its own row: Neo4j rejects the whole batch with "Cannot merge the following node
    because of null property value for 'id'", so one unaccepted invitation would take the team's
    entire user sync with it.

    This goes through the real sync against Neo4j rather than asserting on transform() alone. The
    failure being guarded against is raised by the write, so a transform-level assertion would keep
    passing even if the skip stopped protecting the load.
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
        },
        tests.data.netlify.users.NETLIFY_MEMBERS[0],
    ]

    # Act: no pytest.raises, the point is that this completes
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

    # Assert: the valid member landed, nothing carries a null id, and the membership edge exists
    assert check_nodes(neo4j_session, "NetlifyUser", ["id", "email"]) == {
        (TEST_USER_ID, "alice@example.com"),
    }
    assert (
        neo4j_session.run(
            "MATCH (n:NetlifyUser) WHERE n.id IS NULL RETURN count(n) AS c",
        ).single()["c"]
        == 0
    )
    assert check_rels(
        neo4j_session,
        "NetlifyUser",
        "id",
        "NetlifyAccount",
        "id",
        "MEMBER_OF",
    ) == {(TEST_USER_ID, TEST_ACCOUNT_ID)}
