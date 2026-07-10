from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.salesforce.groups
import cartography.intel.salesforce.users
import tests.data.salesforce.data as test_data
from tests.integration.cartography.intel.salesforce.test_organization import (
    _ensure_local_neo4j_has_test_organization,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789


@patch.object(
    cartography.intel.salesforce.groups,
    "get_members",
    return_value=test_data.SALESFORCE_GROUP_MEMBERS,
)
@patch.object(
    cartography.intel.salesforce.groups,
    "get_groups",
    return_value=test_data.SALESFORCE_GROUPS,
)
def test_sync_salesforce_groups(mock_groups, mock_members, neo4j_session):
    # Arrange
    _ensure_local_neo4j_has_test_organization(neo4j_session)
    cartography.intel.salesforce.users.load_users(
        neo4j_session, test_data.SALESFORCE_USERS, test_data.ORG_ID, TEST_UPDATE_TAG
    )
    common_job_parameters = {"UPDATE_TAG": TEST_UPDATE_TAG, "ORG_ID": test_data.ORG_ID}

    # Act
    cartography.intel.salesforce.groups.sync(
        neo4j_session, Mock(), common_job_parameters
    )

    # Assert nodes
    assert check_nodes(neo4j_session, "SalesforceGroup", ["id", "name"]) == {
        ("00G000000000001AAA", "All Internal Users"),
        ("00G000000000002AAA", "Admins"),
    }

    # Assert user membership
    assert check_rels(
        neo4j_session,
        "SalesforceUser",
        "id",
        "SalesforceGroup",
        "id",
        "MEMBER_OF",
        rel_direction_right=True,
    ) == {
        ("005000000000001AAA", "00G000000000001AAA"),
        ("005000000000002AAA", "00G000000000001AAA"),
        ("005000000000001AAA", "00G000000000002AAA"),
    }

    # Assert nested group membership: Admins is a member of All Internal Users
    assert check_rels(
        neo4j_session,
        "SalesforceGroup",
        "id",
        "SalesforceGroup",
        "id",
        "MEMBER_OF",
        rel_direction_right=True,
    ) == {
        ("00G000000000002AAA", "00G000000000001AAA"),
    }
