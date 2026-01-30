from unittest.mock import patch

import requests

import cartography.intel.openai.adminapikeys
import tests.data.openai.adminapikeys
from tests.integration.cartography.intel.openai.test_users import (
    _ensure_local_neo4j_has_test_users,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_ORG_ID = "org-iwai3meew4phaeNgu8ae"


@patch.object(
    cartography.intel.openai.adminapikeys,
    "get",
    return_value=tests.data.openai.adminapikeys.OPENAI_ADMINAPIKEYS,
)
def test_load_openai_adminapikeys(mock_api, neo4j_session):
    """
    Ensure that adminapikeys actually get loaded
    """

    # Arrange
    api_session = requests.Session()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "BASE_URL": "https://api.openai.con/v1",
        "ORG_ID": TEST_ORG_ID,
    }
    _ensure_local_neo4j_has_test_users(neo4j_session)

    # Act
    cartography.intel.openai.adminapikeys.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
        ORG_ID=TEST_ORG_ID,
    )

    # Assert AdminApiKeys exist
    expected_nodes = {
        ("key_abc", "Administration Key"),
    }
    assert (
        check_nodes(neo4j_session, "OpenAIAdminApiKey", ["id", "name"])
        == expected_nodes
    )

    # Assert AdminApiKeys are linked to the correct org
    expected_rels = {
        ("key_abc", TEST_ORG_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "OpenAIAdminApiKey",
            "id",
            "OpenAIOrganization",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_rels
    )

    expected_rels = {
        (
            "key_abc",
            "user-uJeighaeFair8shaa2av",
        ),
    }
    assert (
        check_rels(
            neo4j_session,
            "OpenAIAdminApiKey",
            "id",
            "OpenAIUser",
            "id",
            "OWNS",
            rel_direction_right=False,
        )
        == expected_rels
    )
