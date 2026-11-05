from unittest.mock import MagicMock
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
        ("pcBEPQVMpki7S1", "sentinelone"),
    }
    assert (
        check_nodes(neo4j_session, "TailscalePostureIntegration", ["id", "provider"])
        == expected_nodes
    )

    # Assert Devices are connected with Tailnet
    expected_rels = {
        ("pcBEPQVMpki7DEVEL", TEST_ORG),
        ("pcBEPQVMpki7S1", TEST_ORG),
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


def test_sync_keeps_postureintegrations_when_endpoint_returns_404(neo4j_session):
    """
    A credential without feature_settings:read gets a 404 from this endpoint. The
    sync must not fail, and must not clean up integrations it could not read.
    """
    # Arrange
    _ensure_local_neo4j_has_test_tailnets(neo4j_session)
    cartography.intel.tailscale.postureintegrations.load_postureintegrations(
        neo4j_session,
        tests.data.tailscale.postureintegrations.TAILSCALE_POSTUREINTEGRATIONS,
        TEST_ORG,
        TEST_UPDATE_TAG,
    )
    not_found = requests.Response()
    not_found.status_code = 404
    api_session = MagicMock(spec=requests.Session)
    api_session.get.return_value = not_found
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG + 1,
        "BASE_URL": "https://fake.tailscale.com",
        "org": TEST_ORG,
    }

    # Act
    cartography.intel.tailscale.postureintegrations.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
        TEST_ORG,
    )

    # Assert
    assert check_nodes(neo4j_session, "TailscalePostureIntegration", ["id"]) == {
        ("pcBEPQVMpki7DEVEL",),
        ("pcBEPQVMpki7S1",),
    }
