from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.salesforce.profiles
import cartography.intel.salesforce.userroles
import cartography.intel.salesforce.users
import tests.data.salesforce.data as test_data
from tests.integration.cartography.intel.salesforce.test_organization import (
    _ensure_local_neo4j_has_test_organization,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789


def _common_job_parameters():
    return {"UPDATE_TAG": TEST_UPDATE_TAG, "ORG_ID": test_data.ORG_ID}


@patch.object(
    cartography.intel.salesforce.users,
    "get",
    return_value=test_data.SALESFORCE_USERS,
)
def test_sync_salesforce_users(mock_get, neo4j_session):
    # Arrange: org + the role/profile nodes the user links to must exist first
    _ensure_local_neo4j_has_test_organization(neo4j_session)
    cartography.intel.salesforce.profiles.load_profiles(
        neo4j_session, test_data.SALESFORCE_PROFILES, test_data.ORG_ID, TEST_UPDATE_TAG
    )
    cartography.intel.salesforce.userroles.load_user_roles(
        neo4j_session,
        test_data.SALESFORCE_USER_ROLES,
        test_data.ORG_ID,
        TEST_UPDATE_TAG,
    )

    # Act
    cartography.intel.salesforce.users.sync(
        neo4j_session, Mock(), _common_job_parameters()
    )

    # Assert users exist
    assert check_nodes(neo4j_session, "SalesforceUser", ["id", "email"]) == {
        ("005000000000001AAA", "hjsimpson@simpson.corp"),
        ("005000000000002AAA", "mbsimpson@simpson.corp"),
    }

    # Users belong to the org
    assert check_rels(
        neo4j_session,
        "SalesforceUser",
        "id",
        "SalesforceOrganization",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        ("005000000000001AAA", test_data.ORG_ID),
        ("005000000000002AAA", test_data.ORG_ID),
    }

    # Users have a profile (canonical HAS_ROLE ontology edge)
    assert check_rels(
        neo4j_session,
        "SalesforceUser",
        "id",
        "SalesforceProfile",
        "id",
        "HAS_ROLE",
        rel_direction_right=True,
    ) == {
        ("005000000000001AAA", "00e000000000001AAA"),
        ("005000000000002AAA", "00e000000000002AAA"),
    }

    # Users are members of a role
    assert check_rels(
        neo4j_session,
        "SalesforceUser",
        "id",
        "SalesforceUserRole",
        "id",
        "MEMBER_OF",
        rel_direction_right=True,
    ) == {
        ("005000000000001AAA", "00E000000000001AAA"),
        ("005000000000002AAA", "00E000000000002AAA"),
    }
