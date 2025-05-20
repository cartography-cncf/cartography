from unittest.mock import patch

import cartography.intel.cloudflare.accounts
import tests.data.cloudflare.accounts
from tests.integration.util import check_nodes

TEST_UPDATE_TAG = 123456789


def _ensure_local_neo4j_has_test_accounts(neo4j_session):
    cartography.intel.cloudflare.accounts.load_accounts(
        neo4j_session,
        tests.data.cloudflare.accounts.CLOUDFLARE_ACCOUNTS,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.cloudflare.accounts,
    "get",
    return_value=tests.data.cloudflare.accounts.CLOUDFLARE_ACCOUNTS,
)
@patch("cloudflare.Cloudflare")
def test_load_cloudflare_accounts(mock_cloudflare, mock_api, neo4j_session):
    """
    Ensure that accounts actually get loaded
    """

    # Arrange
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
    }

    # Act
    cartography.intel.cloudflare.accounts.sync(
        neo4j_session,
        mock_cloudflare,
        common_job_parameters,
    )

    # Assert Accounts exist
    expected_nodes = {
        ("37418d7e-710b-4aa0-a4c0-79ee660690bf", "Simpson Org"),
    }
    assert (
        check_nodes(neo4j_session, "CloudflareAccount", ["id", "name"])
        == expected_nodes
    )
