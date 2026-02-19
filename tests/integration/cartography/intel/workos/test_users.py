from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.workos.users
import tests.data.workos.users
from tests.integration.cartography.intel.workos.test_organizations import (
    _ensure_local_neo4j_has_test_environment,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_CLIENT_ID = "client_1234567890abcdef"


def _ensure_local_neo4j_has_test_users(neo4j_session):
    transformed_users = cartography.intel.workos.users.transform(
        tests.data.workos.users.WORKOS_USERS
    )
    cartography.intel.workos.users.load_users(
        neo4j_session,
        transformed_users,
        TEST_CLIENT_ID,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.workos.users,
    "get",
    return_value=tests.data.workos.users.WORKOS_USERS,
)
def test_load_workos_users(mock_api, neo4j_session):
    """
    Ensure that users actually get loaded
    """
    # Arrange
    _ensure_local_neo4j_has_test_environment(neo4j_session)
    client = MagicMock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "WORKOS_CLIENT_ID": TEST_CLIENT_ID,
    }

    # Act
    cartography.intel.workos.users.sync(
        neo4j_session,
        client,
        common_job_parameters,
    )

    # Assert Users exist
    expected_nodes = {
        ("user_01HXYZ1234567890ABCDEFGHIJ", "hjsimpson@springfield.com"),
        ("user_02HXYZ0987654321ZYXWVUTSRQ", "mbsimpson@springfield.com"),
    }
    assert check_nodes(neo4j_session, "WorkOSUser", ["id", "email"]) == expected_nodes

    # Assert users are linked to the environment
    expected_rels = {
        ("user_01HXYZ1234567890ABCDEFGHIJ", TEST_CLIENT_ID),
        ("user_02HXYZ0987654321ZYXWVUTSRQ", TEST_CLIENT_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "WorkOSUser",
            "id",
            "WorkOSEnvironment",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_rels
    )
