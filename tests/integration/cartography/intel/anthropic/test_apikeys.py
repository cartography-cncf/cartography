from unittest.mock import patch

import requests

import cartography.intel.anthropic.apikeys
import tests.data.anthropic.apikeys
from tests.integration.cartography.intel.anthropic.test_users import (
    _ensure_local_neo4j_has_test_users,
)
from tests.integration.cartography.intel.anthropic.test_workspaces import (
    _ensure_local_neo4j_has_test_workspaces,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_ORG_ID = "8834c225-ea27-405a-aea9-5ed5f07f4858"


@patch.object(
    cartography.intel.anthropic.apikeys,
    "get",
    return_value=(TEST_ORG_ID, tests.data.anthropic.apikeys.ANTHROPIC_APIKEYS),
)
def test_load_anthropic_apikeys(mock_api, neo4j_session):
    """
    Ensure that apikeys actually get loaded
    """

    # Arrange
    api_session = requests.Session()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "BASE_URL": "https://api.anthropic.com/v1",
        "ORG_ID": TEST_ORG_ID,
    }
    _ensure_local_neo4j_has_test_users(neo4j_session)
    _ensure_local_neo4j_has_test_workspaces(neo4j_session)

    # Act
    cartography.intel.anthropic.apikeys.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
    )

    # Assert AdminApiKeys exist
    expected_nodes = {("apikey_01Rj2N8SVvo6BePZj99NhmiT", "Homer Assistant")}
    assert (
        check_nodes(neo4j_session, "AnthropicApiKey", ["id", "name"]) == expected_nodes
    )

    # Assert apikey are linked to the correct org
    expected_rels = {
        ("apikey_01Rj2N8SVvo6BePZj99NhmiT", TEST_ORG_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "AnthropicApiKey",
            "id",
            "AnthropicOrganization",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_rels
    )

    # Assert apikeys are linked to the correct user
    expected_rels = {
        ("apikey_01Rj2N8SVvo6BePZj99NhmiT", "user_EneequohSheesh3Ohtaefu8we2aite")
    }
    assert (
        check_rels(
            neo4j_session,
            "AnthropicApiKey",
            "id",
            "AnthropicUser",
            "id",
            "OWNS",
            rel_direction_right=False,
        )
        == expected_rels
    )

    # Assert apikeys are linked to the correct workspaces
    expected_rels = {
        (
            "apikey_01Rj2N8SVvo6BePZj99NhmiT",
            "wrkspc_01JwQvzr7rXLA5AGx3HKfFUJ",
        ),
    }
    assert (
        check_rels(
            neo4j_session,
            "AnthropicApiKey",
            "id",
            "AnthropicWorkspace",
            "id",
            "CONTAINS",
            rel_direction_right=False,
        )
        == expected_rels
    )
