from unittest.mock import patch

import requests

import cartography.intel.circleci.oidc
import tests.data.circleci.oidc
from tests.integration.cartography.intel.circleci.test_organizations import (
    _ensure_local_neo4j_has_test_orgs,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_BASE_URL = "https://circleci.fake/api/v2"
TEST_ORG_ID = "org-1111-aaaa"


@patch.object(
    cartography.intel.circleci.oidc,
    "get",
    return_value=tests.data.circleci.oidc.CIRCLECI_OIDC_CLAIMS,
)
def test_load_circleci_oidc(mock_api, neo4j_session):
    # Arrange
    api_session = requests.Session()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "BASE_URL": TEST_BASE_URL,
        "ORG_ID": TEST_ORG_ID,
    }
    _ensure_local_neo4j_has_test_orgs(neo4j_session)

    # Act
    cartography.intel.circleci.oidc.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
        TEST_ORG_ID,
    )

    # Assert the org-level OIDC config exists
    assert check_nodes(neo4j_session, "CircleCIOidcConfig", ["id", "scope"]) == {
        (TEST_ORG_ID, "organization"),
    }

    # Assert (Org)-[:RESOURCE]->(OidcConfig)
    assert check_rels(
        neo4j_session,
        "CircleCIOidcConfig",
        "id",
        "CircleCIOrganization",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        (TEST_ORG_ID, TEST_ORG_ID),
    }
