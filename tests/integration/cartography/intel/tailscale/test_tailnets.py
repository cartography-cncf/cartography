from unittest.mock import patch

import requests

import cartography.intel.tailscale.tailnets
import tests.data.tailscale.tailnets
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_TAILNET = "CHANGEME"


@patch.object(
    cartography.intel.tailscale.tailnets,
    "get",
    return_value=tests.data.tailscale.tailnets.TAILSCALE_TAILNETS,
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
        "tailnet": TEST_TAILNET,
    }

    # Act
    cartography.intel.tailscale.tailnets.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
        tailnet,
    )

    # Assert Tailnets exist
    expected_nodes = {
        # CHANGEME: Add here expected node from data
        # (123456, 'john.doe@domain.tld'),
    }
    assert (
        check_nodes(neo4j_session, "TailscaleTailnet", ["id", "email"])
        == expected_nodes
    )
