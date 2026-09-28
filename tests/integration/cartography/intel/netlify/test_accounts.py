from unittest.mock import MagicMock
from unittest.mock import patch

import neo4j
import pytest
import requests

import cartography.intel.netlify.accounts
import tests.data.netlify.accounts
from tests.integration.cartography.intel.netlify.common import TEST_ACCOUNT_ID
from tests.integration.cartography.intel.netlify.common import TEST_ACCOUNT_SLUG
from tests.integration.cartography.intel.netlify.common import TEST_BASE_URL
from tests.integration.cartography.intel.netlify.common import TEST_UPDATE_TAG
from tests.integration.util import check_nodes


@patch.object(
    cartography.intel.netlify.accounts,
    "get_netlify_accounts",
    return_value=tests.data.netlify.accounts.NETLIFY_ACCOUNTS,
)
def test_sync_netlify_account(mock_get, neo4j_session: neo4j.Session) -> None:
    # Arrange
    api_session = MagicMock(spec=requests.Session)

    # Act
    account = cartography.intel.netlify.accounts.sync_netlify_account(
        neo4j_session,
        api_session,
        TEST_BASE_URL,
        TEST_ACCOUNT_SLUG,
        TEST_UPDATE_TAG,
    )

    # Assert the raw payload is handed back so the rest of the sync can scope to it
    assert account["id"] == TEST_ACCOUNT_ID

    # Assert Nodes
    assert check_nodes(neo4j_session, "NetlifyAccount", ["id", "slug", "name"]) == {
        (TEST_ACCOUNT_ID, TEST_ACCOUNT_SLUG, "Example Team"),
    }

    # Assert the security posture fields that motivate this module made it through
    assert check_nodes(
        neo4j_session,
        "NetlifyAccount",
        ["enforce_mfa", "enforce_saml", "org_mfa_enabled", "site_sso_login"],
    ) == {("not_enforced", "not_enforced", False, True)}

    # Assert the ontology label and its projected properties
    assert check_nodes(neo4j_session, "Tenant", ["id", "_ont_name", "_ont_status"]) == {
        (TEST_ACCOUNT_ID, "Example Team", "active"),
    }
    assert check_nodes(neo4j_session, "NetlifyAccount", ["_ont_source"]) == {
        ("netlify",),
    }


@patch.object(
    cartography.intel.netlify.accounts,
    "get_netlify_accounts",
    return_value=tests.data.netlify.accounts.NETLIFY_ACCOUNTS,
)
def test_sync_netlify_account_rejects_unknown_slug(
    mock_get,
    neo4j_session: neo4j.Session,
) -> None:
    """
    An unrecognised slug has to fail loudly. Syncing nothing would let every downstream cleanup
    job delete the previous run's data.
    """
    api_session = MagicMock(spec=requests.Session)

    with pytest.raises(ValueError, match="was not found"):
        cartography.intel.netlify.accounts.sync_netlify_account(
            neo4j_session,
            api_session,
            TEST_BASE_URL,
            "not-a-real-team",
            TEST_UPDATE_TAG,
        )
