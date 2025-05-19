from unittest.mock import patch

import cartography.intel.cloudflare.roles
import tests.data.cloudflare.accounts
import tests.data.cloudflare.roles
from tests.integration.cartography.intel.cloudflare.test_accounts import (
    _ensure_local_neo4j_has_test_accounts,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
ACCOUNT_ID = tests.data.cloudflare.accounts.CLOUDFLARE_ACCOUNTS[0]["id"]


def _ensure_local_neo4j_has_test_roles(neo4j_session):
    cartography.intel.cloudflare.roles.load_roles(
        neo4j_session,
        tests.data.cloudflare.roles.CLOUDFLARE_ROLES,
        ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.cloudflare.roles,
    "get",
    return_value=tests.data.cloudflare.roles.CLOUDFLARE_ROLES,
)
@patch("cloudflare.Cloudflare")
def test_load_cloudflare_roles(mock_cloudflare, mock_api, neo4j_session):
    """
    Ensure that roles actually get loaded
    """

    # Arrange
    common_job_parameters = {"UPDATE_TAG": TEST_UPDATE_TAG, "account_id": ACCOUNT_ID}
    _ensure_local_neo4j_has_test_accounts(neo4j_session)

    # Act
    cartography.intel.cloudflare.roles.sync(
        neo4j_session,
        mock_cloudflare,
        common_job_parameters,
        account_id=ACCOUNT_ID,
    )

    # Assert Roles exist
    expected_nodes = {
        ("590e57f0-d803-4d87-b89b-9a2928f112b5", "Account Administrator"),
    }
    assert (
        check_nodes(neo4j_session, "CloudflareRole", ["id", "name"]) == expected_nodes
    )

    # Assert Roles are connected with Account
    expected_rels = {
        ("590e57f0-d803-4d87-b89b-9a2928f112b5", ACCOUNT_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "CloudflareRole",
            "id",
            "CloudflareAccount",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_rels
    )
