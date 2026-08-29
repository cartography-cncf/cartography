from unittest.mock import patch

import requests

import cartography.intel.circleci.checkout_keys
import tests.data.circleci.checkout_keys
from tests.integration.cartography.intel.circleci.test_organizations import (
    _ensure_local_neo4j_has_test_orgs,
)
from tests.integration.cartography.intel.circleci.test_projects import (
    _ensure_local_neo4j_has_test_projects,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_BASE_URL = "https://circleci.fake/api/v2"
TEST_PROJECT_ID = "proj-1"
TEST_PROJECT_SLUG = "gh/acme/web"


@patch.object(
    cartography.intel.circleci.checkout_keys,
    "get",
    return_value=tests.data.circleci.checkout_keys.CIRCLECI_CHECKOUT_KEYS,
)
def test_load_circleci_checkout_keys(mock_api, neo4j_session):
    # Arrange
    api_session = requests.Session()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "BASE_URL": TEST_BASE_URL,
        "PROJECT_ID": TEST_PROJECT_ID,
    }
    _ensure_local_neo4j_has_test_orgs(neo4j_session)
    _ensure_local_neo4j_has_test_projects(neo4j_session)

    # Act
    cartography.intel.circleci.checkout_keys.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
        TEST_PROJECT_SLUG,
    )

    # Assert checkout keys exist
    assert check_nodes(neo4j_session, "CircleCICheckoutKey", ["id", "type"]) == {
        ("gh/acme/web:c9:0b:1c:4f:d5:65:56:b9", "deploy-key"),
    }

    # Assert (Project)-[:RESOURCE]->(CheckoutKey)
    assert check_rels(
        neo4j_session,
        "CircleCICheckoutKey",
        "id",
        "CircleCIProject",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        ("gh/acme/web:c9:0b:1c:4f:d5:65:56:b9", TEST_PROJECT_ID),
    }
