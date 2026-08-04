from unittest.mock import patch

import cartography.intel.cloudflare.workerroutes
import tests.data.cloudflare.accounts
import tests.data.cloudflare.workerroutes
import tests.data.cloudflare.zones
from tests.integration.cartography.intel.cloudflare.test_accounts import (
    _ensure_local_neo4j_has_test_accounts,
)
from tests.integration.cartography.intel.cloudflare.test_workerscripts import (
    _ensure_local_neo4j_has_test_workerscripts,
)
from tests.integration.cartography.intel.cloudflare.test_zones import (
    _ensure_local_neo4j_has_test_zones,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
ACCOUNT_ID = tests.data.cloudflare.accounts.CLOUDFLARE_ACCOUNTS[0]["id"]
ZONE_ID = tests.data.cloudflare.zones.CLOUDFLARE_ZONES[0]["id"]


def _ensure_local_neo4j_has_test_workerroutes(neo4j_session):
    cartography.intel.cloudflare.workerroutes.load_workerroutes(
        neo4j_session,
        cartography.intel.cloudflare.workerroutes.transform_routes(
            tests.data.cloudflare.workerroutes.CLOUDFLARE_WORKER_ROUTES,
            ACCOUNT_ID,
        ),
        ACCOUNT_ID,
        ZONE_ID,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.cloudflare.workerroutes,
    "get",
    return_value=tests.data.cloudflare.workerroutes.CLOUDFLARE_WORKER_ROUTES,
)
@patch("cloudflare.Cloudflare")
def test_load_cloudflare_workerroutes(mock_cloudflare, mock_api, neo4j_session):
    """
    Ensure that Worker routes get loaded and linked to the scripts they invoke
    """

    # Arrange
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "account_id": ACCOUNT_ID,
    }
    _ensure_local_neo4j_has_test_accounts(neo4j_session)
    _ensure_local_neo4j_has_test_zones(neo4j_session)
    _ensure_local_neo4j_has_test_workerscripts(neo4j_session)

    # Act
    cartography.intel.cloudflare.workerroutes.sync(
        neo4j_session,
        mock_cloudflare,
        common_job_parameters,
        ACCOUNT_ID,
        tests.data.cloudflare.zones.CLOUDFLARE_ZONES,
    )

    # Assert routes exist
    expected_nodes = {
        (
            "7c1e5f3a9b2d4c6e8f0a1b2c3d4e5f60",
            "photos.simpson.corp/resize/*",
            "donut-image-resizer",
        ),
        (
            "8d2f6a4b0c3e5d7f9a1b2c3d4e5f6071",
            "api.simpson.corp/reactor/*",
            "reactor-status-api",
        ),
        ("9e3a7b5c1d4f6e8a0b2c3d4e5f607182", "legacy.simpson.corp/*", None),
    }
    assert (
        check_nodes(
            neo4j_session,
            "CloudflareWorkerRoute",
            ["id", "pattern", "script"],
        )
        == expected_nodes
    )

    # Assert routes are connected with Zone
    expected_zone_rels = {
        ("7c1e5f3a9b2d4c6e8f0a1b2c3d4e5f60", ZONE_ID),
        ("8d2f6a4b0c3e5d7f9a1b2c3d4e5f6071", ZONE_ID),
        ("9e3a7b5c1d4f6e8a0b2c3d4e5f607182", ZONE_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "CloudflareWorkerRoute",
            "id",
            "CloudflareZone",
            "id",
            "HAS_ROUTE",
            rel_direction_right=False,
        )
        == expected_zone_rels
    )

    # Assert only the routes with a script attached point at one
    expected_script_rels = {
        (
            "7c1e5f3a9b2d4c6e8f0a1b2c3d4e5f60",
            f"{ACCOUNT_ID}/donut-image-resizer",
        ),
        (
            "8d2f6a4b0c3e5d7f9a1b2c3d4e5f6071",
            f"{ACCOUNT_ID}/reactor-status-api",
        ),
    }
    assert (
        check_rels(
            neo4j_session,
            "CloudflareWorkerRoute",
            "id",
            "CloudflareWorkerScript",
            "id",
            "ROUTES_TO",
            rel_direction_right=True,
        )
        == expected_script_rels
    )
