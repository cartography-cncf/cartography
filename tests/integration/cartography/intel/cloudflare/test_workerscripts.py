from unittest.mock import patch

import cartography.intel.cloudflare.workerscripts
import tests.data.cloudflare.accounts
import tests.data.cloudflare.workerscripts
from tests.integration.cartography.intel.cloudflare.test_accounts import (
    _ensure_local_neo4j_has_test_accounts,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
ACCOUNT_ID = tests.data.cloudflare.accounts.CLOUDFLARE_ACCOUNTS[0]["id"]


def _ensure_local_neo4j_has_test_workerscripts(neo4j_session):
    cartography.intel.cloudflare.workerscripts.load_workerscripts(
        neo4j_session,
        cartography.intel.cloudflare.workerscripts.transform_scripts(
            tests.data.cloudflare.workerscripts.CLOUDFLARE_WORKER_SCRIPTS,
            ACCOUNT_ID,
        ),
        ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.cloudflare.workerscripts,
    "get",
    return_value=tests.data.cloudflare.workerscripts.CLOUDFLARE_WORKER_SCRIPTS,
)
@patch("cloudflare.Cloudflare")
def test_load_cloudflare_workerscripts(mock_cloudflare, mock_api, neo4j_session):
    """
    Ensure that Worker scripts actually get loaded
    """

    # Arrange
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "account_id": ACCOUNT_ID,
    }
    _ensure_local_neo4j_has_test_accounts(neo4j_session)

    # Act
    cartography.intel.cloudflare.workerscripts.sync(
        neo4j_session,
        mock_cloudflare,
        common_job_parameters,
        ACCOUNT_ID,
    )

    # Assert scripts exist
    expected_nodes = {
        (
            f"{ACCOUNT_ID}/donut-image-resizer",
            "donut-image-resizer",
            "c1f8a2b3d4e5f6a7b8c9d0e1f2a3b4c5",
            "standard",
            True,
        ),
        (
            f"{ACCOUNT_ID}/reactor-status-api",
            "reactor-status-api",
            "d2e9b3c4e5f6a7b8c9d0e1f2a3b4c5d6",
            "bundled",
            False,
        ),
    }
    assert (
        check_nodes(
            neo4j_session,
            "CloudflareWorkerScript",
            ["id", "name", "tag", "usage_model", "observability_enabled"],
        )
        == expected_nodes
    )

    # Assert scripts are connected with Account
    expected_rels = {
        (f"{ACCOUNT_ID}/donut-image-resizer", ACCOUNT_ID),
        (f"{ACCOUNT_ID}/reactor-status-api", ACCOUNT_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "CloudflareWorkerScript",
            "id",
            "CloudflareAccount",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_rels
    )

    # Assert the Function ontology label and its normalized properties land
    result = neo4j_session.run(
        """
        MATCH (s:CloudflareWorkerScript:Function)
        RETURN s._ont_name AS name, s._ont_deployment_type AS deployment_type
        ORDER BY name
        """
    )
    assert [dict(record) for record in result] == [
        {"name": "donut-image-resizer", "deployment_type": "code"},
        {"name": "reactor-status-api", "deployment_type": "code"},
    ]
