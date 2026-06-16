from unittest.mock import patch

import requests

import cartography.intel.circleci.organizations
import tests.data.circleci.organizations
from tests.integration.util import check_nodes

TEST_UPDATE_TAG = 123456789
TEST_BASE_URL = "https://circleci.fake/api/v2"


def _ensure_local_neo4j_has_test_orgs(neo4j_session):
    orgs = cartography.intel.circleci.organizations.transform(
        tests.data.circleci.organizations.CIRCLECI_COLLABORATIONS,
    )
    cartography.intel.circleci.organizations.load_organizations(
        neo4j_session,
        orgs,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.circleci.organizations,
    "get",
    return_value=tests.data.circleci.organizations.CIRCLECI_COLLABORATIONS,
)
def test_load_circleci_organizations(mock_api, neo4j_session):
    # Arrange
    api_session = requests.Session()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "BASE_URL": TEST_BASE_URL,
    }

    # Act
    cartography.intel.circleci.organizations.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
    )

    # Assert organizations exist with their slug
    assert check_nodes(neo4j_session, "CircleCIOrganization", ["id", "slug"]) == {
        ("org-1111-aaaa", "gh/acme"),
        ("org-2222-bbbb", "bb/beta"),
    }
