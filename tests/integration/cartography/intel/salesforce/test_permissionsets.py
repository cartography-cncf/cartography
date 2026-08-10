from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.salesforce.permissionsets
import cartography.intel.salesforce.users
import tests.data.salesforce.data as test_data
from tests.integration.cartography.intel.salesforce.test_organization import (
    _ensure_local_neo4j_has_test_organization,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789


@patch.object(
    cartography.intel.salesforce.permissionsets,
    "get_assignments",
    return_value=test_data.SALESFORCE_PERMISSION_SET_ASSIGNMENTS,
)
@patch.object(
    cartography.intel.salesforce.permissionsets,
    "get_permission_sets",
    return_value=test_data.SALESFORCE_PERMISSION_SETS,
)
def test_sync_salesforce_permission_sets(mock_sets, mock_assignments, neo4j_session):
    # Arrange: org + the assignee user must exist for the HAS_ROLE edge
    _ensure_local_neo4j_has_test_organization(neo4j_session)
    cartography.intel.salesforce.users.load_users(
        neo4j_session, test_data.SALESFORCE_USERS, test_data.ORG_ID, TEST_UPDATE_TAG
    )
    common_job_parameters = {"UPDATE_TAG": TEST_UPDATE_TAG, "ORG_ID": test_data.ORG_ID}

    # Act
    cartography.intel.salesforce.permissionsets.sync(
        neo4j_session, Mock(), common_job_parameters
    )

    # Assert nodes
    assert check_nodes(neo4j_session, "SalesforcePermissionSet", ["id", "name"]) == {
        ("0PS000000000001AAA", "API_Access"),
    }

    # Assert assignment edge: Homer HAS_ROLE the API_Access permission set
    assert check_rels(
        neo4j_session,
        "SalesforceUser",
        "id",
        "SalesforcePermissionSet",
        "id",
        "HAS_ROLE",
        rel_direction_right=True,
    ) == {
        ("005000000000001AAA", "0PS000000000001AAA"),
    }
