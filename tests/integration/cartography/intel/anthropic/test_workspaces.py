from unittest.mock import patch

import pytest
import requests

import cartography.intel.anthropic.apikeys
import cartography.intel.anthropic.workspaces
import tests.data.anthropic.apikeys
import tests.data.anthropic.workspaces
from tests.integration.cartography.intel.anthropic.test_users import (
    _ensure_local_neo4j_has_test_users,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_ORG_ID = "8834c225-ea27-405a-aea9-5ed5f07f4858"


def _ensure_local_neo4j_has_test_workspaces(neo4j_session):
    cartography.intel.anthropic.workspaces.load_workspaces(
        neo4j_session,
        tests.data.anthropic.workspaces.ANTHROPIC_WORKSPACES,
        TEST_ORG_ID,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.anthropic.workspaces,
    "get_workspace_users",
    return_value=tests.data.anthropic.workspaces.ANTHROPIC_WORKSPACES_MEMBERS,
)
@patch.object(
    cartography.intel.anthropic.workspaces,
    "get",
    return_value=(TEST_ORG_ID, tests.data.anthropic.workspaces.ANTHROPIC_WORKSPACES),
)
def test_load_anthropic_workspaces(mock_api, mock_api_members, neo4j_session):
    """
    Ensure that workspaces actually get loaded
    """

    # Arrange
    api_session = requests.Session()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "BASE_URL": "https://api.anthropic.com/v1",
    }
    _ensure_local_neo4j_has_test_users(neo4j_session)

    # Act
    cartography.intel.anthropic.workspaces.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
    )

    # Assert Workspaces exist
    expected_nodes = {
        (
            "wrkspc_01JwQvzr7rXLA5AGx3HKfFUJ",
            "Springfield Nuclear Power Plant",
        ),
    }
    assert (
        check_nodes(neo4j_session, "AnthropicWorkspace", ["id", "name"])
        == expected_nodes
    )

    # Assert workspaces are linked to the correct org
    expected_rels = {
        ("wrkspc_01JwQvzr7rXLA5AGx3HKfFUJ", TEST_ORG_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "AnthropicWorkspace",
            "id",
            "AnthropicOrganization",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_rels
    )

    # Assert workspaces are linked to the correct users
    expected_rels = {
        ("user_EneequohSheesh3Ohtaefu8we2aite", "wrkspc_01JwQvzr7rXLA5AGx3HKfFUJ"),
        ("user_Oov3aYewo6ZuoGh8thaiV1uNoy1aXe", "wrkspc_01JwQvzr7rXLA5AGx3HKfFUJ"),
    }
    assert (
        check_rels(
            neo4j_session,
            "AnthropicUser",
            "id",
            "AnthropicWorkspace",
            "id",
            "MEMBER_OF",
            rel_direction_right=True,
        )
        == expected_rels
    )
    expected_rels = {
        ("user_EneequohSheesh3Ohtaefu8we2aite", "wrkspc_01JwQvzr7rXLA5AGx3HKfFUJ")
    }
    assert (
        check_rels(
            neo4j_session,
            "AnthropicUser",
            "id",
            "AnthropicWorkspace",
            "id",
            "ADMIN_OF",
            rel_direction_right=True,
        )
        == expected_rels
    )


ORGANIZATIONS_URL = "https://api.anthropic.com/v1/organizations/workspaces"
TOKEN_URL = "https://api.anthropic.com/v1/oauth/token"
COMMON_JOB_PARAMETERS = {
    "UPDATE_TAG": TEST_UPDATE_TAG + 1,
    "BASE_URL": "https://api.anthropic.com/v1",
    "ORG_ID": TEST_ORG_ID,
}


def _http_error(status_code: int, url: str) -> requests.HTTPError:
    response = requests.Response()
    response.status_code = status_code
    response.url = url
    return requests.HTTPError(response=response)


def _ensure_local_neo4j_has_test_apikeys(neo4j_session):
    cartography.intel.anthropic.apikeys.load_apikeys(
        neo4j_session,
        tests.data.anthropic.apikeys.ANTHROPIC_APIKEYS,
        TEST_ORG_ID,
        TEST_UPDATE_TAG,
    )


@pytest.mark.parametrize(
    ("module", "seed", "label", "ids"),
    [
        (
            cartography.intel.anthropic.workspaces,
            _ensure_local_neo4j_has_test_workspaces,
            "AnthropicWorkspace",
            {(w["id"],) for w in tests.data.anthropic.workspaces.ANTHROPIC_WORKSPACES},
        ),
        (
            cartography.intel.anthropic.apikeys,
            _ensure_local_neo4j_has_test_apikeys,
            "AnthropicApiKey",
            {(k["id"],) for k in tests.data.anthropic.apikeys.ANTHROPIC_APIKEYS},
        ),
    ],
)
@pytest.mark.parametrize("status_code", [403, 404])
def test_sync_skips_endpoints_an_enterprise_org_lacks(
    module, seed, label, ids, status_code, neo4j_session
):
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    _ensure_local_neo4j_has_test_users(neo4j_session)
    seed(neo4j_session)

    with patch.object(
        module, "get", side_effect=_http_error(status_code, ORGANIZATIONS_URL)
    ):
        module.sync(neo4j_session, requests.Session(), dict(COMMON_JOB_PARAMETERS))

    assert check_nodes(neo4j_session, label, ["id"]) == ids


@pytest.mark.parametrize(
    ("status_code", "url"),
    [(401, ORGANIZATIONS_URL), (403, TOKEN_URL)],
)
def test_sync_raises_when_the_credential_is_rejected(status_code, url, neo4j_session):
    with (
        patch.object(
            cartography.intel.anthropic.workspaces,
            "get",
            side_effect=_http_error(status_code, url),
        ),
        pytest.raises(requests.HTTPError),
    ):
        cartography.intel.anthropic.workspaces.sync(
            neo4j_session, requests.Session(), dict(COMMON_JOB_PARAMETERS)
        )
