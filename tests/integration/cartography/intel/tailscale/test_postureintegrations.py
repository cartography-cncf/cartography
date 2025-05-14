from unittest.mock import patch

import requests

import cartography.intel.tailscale.postureintegrations
import tests.data.tailscale.postureintegrations
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_TAILNET = "CHANGEME"


@patch.object(
    cartography.intel.tailscale.postureintegrations,
    "get",
    return_value=tests.data.tailscale.postureintegrations.TAILSCALE_POSTUREINTEGRATIONS,
)
def test_load_tailscale_postureintegrations(mock_api, neo4j_session):
    """
    Ensure that postureintegrations actually get loaded
    """

    # Arrange
    api_session = requests.Session()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "BASE_URL": "https://fake.tailscale.com",
        "tailnet": TEST_TAILNET,
    }

    # Act
    cartography.intel.tailscale.postureintegrations.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
        tailnet,
    )

    # Assert PostureIntegrations exist
    expected_nodes = {
        # CHANGEME: Add here expected node from data
        # (123456, 'john.doe@domain.tld'),
    }
    assert (
        check_nodes(neo4j_session, "TailscalePostureIntegration", ["id", "email"])
        == expected_nodes
    )
