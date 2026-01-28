from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.pagerduty.users
import tests.data.pagerduty.users
from tests.integration.util import check_nodes

TEST_UPDATE_TAG = 123456789


def _ensure_local_neo4j_has_test_users(neo4j_session):
    cartography.intel.pagerduty.users.load_user_data(
        neo4j_session,
        tests.data.pagerduty.users.GET_USERS_DATA,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.pagerduty.users,
    "get_users",
    return_value=tests.data.pagerduty.users.GET_USERS_DATA,
)
def test_load_user_data(mock_get, neo4j_session):
    # Arrange
    api_session = Mock()
    common_job_parameters = {"UPDATE_TAG": TEST_UPDATE_TAG}

    # Act
    cartography.intel.pagerduty.users.sync_users(
        neo4j_session, TEST_UPDATE_TAG, api_session, common_job_parameters
    )

    # Assert nodes exists
    expected_nodes = {
        ("PAM4FGS", "126_dvm_kyler_kuhn@beahan.name"),
        ("PXPGF42", "125.greenholt.earline@graham.name"),
    }
    assert (
        check_nodes(neo4j_session, "PagerDutyUser", ["id", "email"]) == expected_nodes
    )
