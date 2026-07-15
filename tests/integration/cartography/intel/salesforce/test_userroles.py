from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.salesforce.userroles
import tests.data.salesforce.data as test_data
from tests.integration.cartography.intel.salesforce.test_organization import (
    _ensure_local_neo4j_has_test_organization,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789


@patch.object(
    cartography.intel.salesforce.userroles,
    "get",
    return_value=test_data.SALESFORCE_USER_ROLES,
)
def test_sync_salesforce_user_roles(mock_get, neo4j_session):
    # Arrange
    _ensure_local_neo4j_has_test_organization(neo4j_session)
    common_job_parameters = {"UPDATE_TAG": TEST_UPDATE_TAG, "ORG_ID": test_data.ORG_ID}

    # Act
    cartography.intel.salesforce.userroles.sync(
        neo4j_session, Mock(), common_job_parameters
    )

    # Assert nodes
    assert check_nodes(neo4j_session, "SalesforceUserRole", ["id", "name"]) == {
        ("00E000000000001AAA", "CEO"),
        ("00E000000000002AAA", "VP Sales"),
    }

    # Assert role hierarchy: VP Sales reports up to CEO
    assert check_rels(
        neo4j_session,
        "SalesforceUserRole",
        "id",
        "SalesforceUserRole",
        "id",
        "MEMBER_OF",
        rel_direction_right=True,
    ) == {
        ("00E000000000002AAA", "00E000000000001AAA"),
    }
