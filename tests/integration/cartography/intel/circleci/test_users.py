from unittest.mock import patch

import requests

import cartography.intel.circleci.users
import tests.data.circleci.users
from tests.integration.cartography.intel.circleci.test_organizations import (
    _ensure_local_neo4j_has_test_orgs,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_BASE_URL = "https://circleci.fake/api/v2"
TEST_ORG_ID = "org-1111-aaaa"


@patch.object(
    cartography.intel.circleci.users,
    "get",
    return_value=tests.data.circleci.users.CIRCLECI_ME,
)
def test_load_circleci_users(mock_api, neo4j_session):
    # Arrange
    api_session = requests.Session()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "BASE_URL": TEST_BASE_URL,
        "ORG_ID": TEST_ORG_ID,
    }
    _ensure_local_neo4j_has_test_orgs(neo4j_session)

    # Act
    cartography.intel.circleci.users.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
        TEST_ORG_ID,
    )

    # Assert the token owner exists
    assert check_nodes(neo4j_session, "CircleCIUser", ["id", "login"]) == {
        ("user-9999-zzzz", "alice"),
    }

    # Assert (Org)-[:RESOURCE]->(User)
    assert check_rels(
        neo4j_session,
        "CircleCIUser",
        "id",
        "CircleCIOrganization",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        ("user-9999-zzzz", TEST_ORG_ID),
    }
