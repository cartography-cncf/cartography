from unittest.mock import patch

import requests

import cartography.intel.tailscale.postureintegrations
import tests.data.tailscale.postureintegrations
from tests.integration.cartography.intel.tailscale.test_tailnets import (
    _ensure_local_neo4j_has_test_tailnets,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_ORG = "simpson.corp"


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
        "org": TEST_ORG,
    }
    _ensure_local_neo4j_has_test_tailnets(neo4j_session)

    # Act
    cartography.intel.tailscale.postureintegrations.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
        TEST_ORG,
    )

    # Assert PostureIntegrations exist
    expected_nodes = {
        ("pcBEPQVMpki7DEVEL", "falcon"),
    }
    assert (
        check_nodes(neo4j_session, "TailscalePostureIntegration", ["id", "provider"])
        == expected_nodes
    )

    # Assert Devices are connected with Tailnet
    expected_rels = {
        ("pcBEPQVMpki7DEVEL", TEST_ORG),
    }
    assert (
        check_rels(
            neo4j_session,
            "TailscalePostureIntegration",
            "id",
            "TailscaleTailnet",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_rels
    )
