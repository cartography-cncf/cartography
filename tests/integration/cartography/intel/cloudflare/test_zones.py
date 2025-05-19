from unittest.mock import patch

import cartography.intel.cloudflare.zones
import tests.data.cloudflare.zones
from tests.integration.cartography.intel.cloudflare.test_accounts import (
    _ensure_local_neo4j_has_test_accounts,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
ACCOUNT_ID = tests.data.cloudflare.accounts.CLOUDFLARE_ACCOUNTS[0]["id"]


def _ensure_local_neo4j_has_test_zones(neo4j_session):
    cartography.intel.cloudflare.zones.load_zones(
        neo4j_session,
        tests.data.cloudflare.zones.CLOUDFLARE_ZONES,
        ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.cloudflare.zones,
    "get",
    return_value=tests.data.cloudflare.zones.CLOUDFLARE_ZONES,
)
@patch("cloudflare.Cloudflare")
def test_load_cloudflare_zones(mock_cloudflare, mock_api, neo4j_session):
    """
    Ensure that zones actually get loaded
    """

    # Arrange
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "account_id": ACCOUNT_ID,
    }
    _ensure_local_neo4j_has_test_accounts(neo4j_session)

    # Act
    cartography.intel.cloudflare.zones.sync(
        neo4j_session,
        mock_cloudflare,
        common_job_parameters,
        ACCOUNT_ID,
    )

    # Assert Zones exist
    expected_nodes = {
        ("be68b067-5b2b-49f7-ad89-943d501dc900", "simpson.corp"),
    }
    assert (
        check_nodes(neo4j_session, "CloudflareZone", ["id", "name"]) == expected_nodes
    )

    # Assert Zones are connected with Account
    expected_rels = {
        ("be68b067-5b2b-49f7-ad89-943d501dc900", ACCOUNT_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "CloudflareZone",
            "id",
            "CloudflareAccount",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_rels
    )
