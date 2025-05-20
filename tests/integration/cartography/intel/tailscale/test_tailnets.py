from unittest.mock import patch

import requests

import cartography.intel.tailscale.tailnets
import tests.data.tailscale.tailnets
from tests.integration.util import check_nodes

TEST_UPDATE_TAG = 123456789
TEST_ORG = "simpson.corp"


def _ensure_local_neo4j_has_test_tailnets(neo4j_session):
    cartography.intel.tailscale.tailnets.load_tailnets(
        neo4j_session,
        [tests.data.tailscale.tailnets.TAILSCALE_TAILNET],
        TEST_ORG,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.tailscale.tailnets,
    "get",
    return_value=tests.data.tailscale.tailnets.TAILSCALE_TAILNET,
)
def test_load_tailscale_tailnets(mock_api, neo4j_session):
    """
    Ensure that tailnets actually get loaded
    """

    # Arrange
    api_session = requests.Session()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "BASE_URL": "https://fake.tailscale.com",
        "org": TEST_ORG,
    }

    # Act
    cartography.intel.tailscale.tailnets.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
        TEST_ORG,
    )

    # Assert Tailnets exist
    expected_nodes = {
        ("simpson.corp",),
    }
    assert (
        check_nodes(
            neo4j_session,
            "TailscaleTailnet",
            [
                "id",
            ],
        )
        == expected_nodes
    )
