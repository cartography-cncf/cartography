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


def _ensure_local_neo4j_has_test_users(neo4j_session: neo4j.Session) -> None:
    cartography.intel.netlify.users.load_netlify_users(
        neo4j_session,
        cartography.intel.netlify.users.transform_netlify_users(
            tests.data.netlify.users.NETLIFY_MEMBERS,
        ),
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )


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

    # Assert Nodes: keyed on the person's user_id, not the membership id
    assert check_nodes(
        neo4j_session,
        "NetlifyUser",
        ["id", "email", "full_name", "mfa_enabled", "pending"],
    ) == {(TEST_USER_ID, "alice@example.com", "Alice Example", False, False)}

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
               r.membership_id AS membership_id
        """,
    ).single()
    assert membership["role"] == "Owner"
    assert membership["site_access"] == "all"
    assert membership["membership_id"] == _MEMBERSHIP_ID

    # Assert the ontology label and its projected properties. has_mfa and the inverted
    # `pending` are what an MFA-coverage rule reads.
    assert check_nodes(
        neo4j_session,
        "UserAccount",
        ["id", "_ont_email", "_ont_has_mfa", "_ont_active", "_ont_source"],
    ) == {(TEST_USER_ID, "alice@example.com", False, True, "netlify")}
