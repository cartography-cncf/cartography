from unittest.mock import patch

import requests

import cartography.intel.circleci.groups
import tests.data.circleci.groups
from tests.integration.cartography.intel.circleci.test_organizations import (
    _ensure_local_neo4j_has_test_orgs,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_BASE_URL = "https://circleci.fake/api/v2"
TEST_ORG_ID = "org-1111-aaaa"


@patch.object(
    cartography.intel.circleci.groups,
    "get",
    return_value=tests.data.circleci.groups.CIRCLECI_GROUPS,
)
def test_load_circleci_groups(mock_api, neo4j_session):
    # Arrange
    api_session = requests.Session()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "BASE_URL": TEST_BASE_URL,
        "ORG_ID": TEST_ORG_ID,
    }
    _ensure_local_neo4j_has_test_orgs(neo4j_session)

    # Act
    cartography.intel.circleci.groups.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
        TEST_ORG_ID,
    )

    # Assert
    assert check_nodes(neo4j_session, "CircleCIGroup", ["id", "name"]) == {
        ("grp-1", "platform"),
        ("grp-2", "security"),
    }
    assert check_rels(
        neo4j_session,
        "CircleCIGroup",
        "id",
        "CircleCIOrganization",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        ("grp-1", TEST_ORG_ID),
        ("grp-2", TEST_ORG_ID),
    }
