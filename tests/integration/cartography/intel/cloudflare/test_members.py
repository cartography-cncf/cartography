from unittest.mock import patch

import cartography.intel.cloudflare.members
import tests.data.cloudflare.accounts
import tests.data.cloudflare.members
import tests.data.cloudflare.roles
from tests.integration.cartography.intel.cloudflare.test_accounts import (
    _ensure_local_neo4j_has_test_accounts,
)
from tests.integration.cartography.intel.cloudflare.test_roles import (
    _ensure_local_neo4j_has_test_roles,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
ACCOUNT_ID = tests.data.cloudflare.accounts.CLOUDFLARE_ACCOUNTS[0]["id"]
ROLE_ID = tests.data.cloudflare.roles.CLOUDFLARE_ROLES[0]["id"]


@patch.object(
    cartography.intel.cloudflare.members,
    "get",
    return_value=tests.data.cloudflare.members.CLOUDFLARE_MEMBERS,
)
@patch("cloudflare.Cloudflare")
def test_load_cloudflare_members(mock_cloudflare, mock_api, neo4j_session):
    """
    Ensure that members actually get loaded
    """

    # Arrange
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "account_id": ACCOUNT_ID,
    }
    _ensure_local_neo4j_has_test_accounts(neo4j_session)
    _ensure_local_neo4j_has_test_roles(neo4j_session)

    # Act
    cartography.intel.cloudflare.members.sync(
        neo4j_session,
        mock_cloudflare,
        common_job_parameters,
        ACCOUNT_ID,
    )

    # Assert Members exist
    expected_nodes = {
        ("1ddb5796-70f4-4325-9448-3da69737912d", "hjsimpson@simpson.corp"),
        ("888a46f2-4465-4efa-89f5-0281db1a3fcd", "mbsimpson@simpson.corp"),
    }

    assert (
        check_nodes(neo4j_session, "CloudflareMember", ["id", "email"])
        == expected_nodes
    )

    # Assert Members are connected with Account
    expected_rels = {
        ("888a46f2-4465-4efa-89f5-0281db1a3fcd", ACCOUNT_ID),
        ("1ddb5796-70f4-4325-9448-3da69737912d", ACCOUNT_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "CloudflareMember",
            "id",
            "CloudflareAccount",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_rels
    )

    # Assert Members are connected with Role
    expected_rels = {
        ("888a46f2-4465-4efa-89f5-0281db1a3fcd", ROLE_ID),
        ("1ddb5796-70f4-4325-9448-3da69737912d", ROLE_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "CloudflareMember",
            "id",
            "CloudflareRole",
            "id",
            "HAS_ROLE",
            rel_direction_right=True,
        )
        == expected_rels
    )
