from unittest.mock import patch

import requests

import cartography.intel.anthropic.apikeys
import tests.data.anthropic.apikeys
from tests.integration.cartography.intel.anthropic.test_serviceaccounts import (
    _ensure_local_neo4j_has_test_service_accounts,
)
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
    _ensure_local_neo4j_has_test_service_accounts(neo4j_session)

    # Act
    cartography.intel.anthropic.apikeys.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
    )

    # Assert AdminApiKeys exist, carrying expiry and the principal they act as
    expected_nodes = {
        (
            "apikey_01Rj2N8SVvo6BePZj99NhmiT",
            "Homer Assistant",
            None,
            "user",
        ),
        (
            "apikey_01Wq7X2ZTbn4LcVpM8sKdYhE",
            "Reactor Telemetry Collector",
            "2026-01-14T08:12:03.114509Z",
            "service_account",
        ),
    }
    assert (
        check_nodes(
            neo4j_session,
            "AnthropicApiKey",
            ["id", "name", "expires_at", "principal_type"],
        )
        == expected_nodes
    )

    # Assert apikey are linked to the correct org
    expected_rels = {
        ("apikey_01Rj2N8SVvo6BePZj99NhmiT", TEST_ORG_ID),
        ("apikey_01Wq7X2ZTbn4LcVpM8sKdYhE", TEST_ORG_ID),
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
        ("apikey_01Rj2N8SVvo6BePZj99NhmiT", "user_EneequohSheesh3Ohtaefu8we2aite"),
        ("apikey_01Wq7X2ZTbn4LcVpM8sKdYhE", "user_Oov3aYewo6ZuoGh8thaiV1uNoy1aXe"),
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
    # Canonical ontology edge: (:APIKey)-[:OWNED_BY]->(:UserAccount). Only the
    # human-owned key gets one: a key acting as a service account is owned by that
    # service account, not by the human who happened to create it, so it must not
    # report two owners.
    assert check_rels(
        neo4j_session,
        "AnthropicApiKey",
        "id",
        "AnthropicUser",
        "id",
        "OWNED_BY",
        rel_direction_right=True,
    ) == {("apikey_01Rj2N8SVvo6BePZj99NhmiT", "user_EneequohSheesh3Ohtaefu8we2aite")}

    # Assert the service-account-owned key edges to its principal, and the
    # human-owned one does not
    assert check_rels(
        neo4j_session,
        "AnthropicApiKey",
        "id",
        "AnthropicServiceAccount",
        "id",
        "OWNED_BY",
        rel_direction_right=True,
    ) == {("apikey_01Wq7X2ZTbn4LcVpM8sKdYhE", "svac_01Nb5RtYuIoPaSdFgHjKlZxC")}

    # Assert apikeys are linked to the correct workspaces
    expected_rels = {
        (
            "apikey_01Rj2N8SVvo6BePZj99NhmiT",
            "wrkspc_01JwQvzr7rXLA5AGx3HKfFUJ",
        ),
        (
            "apikey_01Wq7X2ZTbn4LcVpM8sKdYhE",
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
