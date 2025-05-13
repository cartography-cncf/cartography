from unittest.mock import patch

import requests

import cartography.intel.cloudflare.members
import tests.data.cloudflare.members
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
ACCOUNT_ID = "37418d7e-710b-4aa0-a4c0-79ee660690bf"


@patch.object(
    cartography.intel.cloudflare.members,
    "get",
    return_value=tests.data.cloudflare.members.CLOUDFLARE_MEMBERS,
)
def test_load_cloudflare_members(mock_api, neo4j_session):
    """
    Ensure that members actually get loaded
    """

    # Arrange
    api_session = requests.Session()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "BASE_URL": "https://fake.cloudflare.com",
    }

    # Act
    cartography.intel.cloudflare.members.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
        ACCOUNT_ID,
    )

    # Assert Members exist
    expected_nodes = {
        ("888a46f2-4465-4efa-89f5-0281db1a3fcd", "mbsimpson@simpson.corp"),
        ("1ddb5796-70f4-4325-9448-3da69737912d", "hjsimpson@simpson.corp"),
    }

    assert (
        check_nodes(neo4j_session, "CloudflareMember", ["id", "email"])
        == expected_nodes
    )

    # Assert Members are connected with Account
    expected_rels = {
        ("888a46f2-4465-4efa-89f5-0281db1a3fcd", ACCOUNT_ID),
        ("1ddb5796-70f4-4325-9448-3da69737912d", ACCOUNT_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "CloudflareMember",
            "id",
            "CloudflareAccount",
            "id",
            "RESOURCE",
            rel_direction_right=True,
        )
        == expected_rels
    )
