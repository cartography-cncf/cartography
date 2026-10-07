from unittest.mock import AsyncMock
from unittest.mock import MagicMock

from okta.models.admin_console_settings import AdminConsoleSettings

from cartography.intel.okta.organization import sync_okta_organization
from tests.integration.util import check_nodes

TEST_ORG_ID = "test-okta-org-id"
TEST_UPDATE_TAG = 123456789


def test_sync_okta_organization_with_admin_console_settings(neo4j_session) -> None:
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    okta_client = MagicMock()
    okta_client.get_first_party_app_settings = AsyncMock(
        return_value=(
            AdminConsoleSettings(
                session_idle_timeout_minutes=15,
                session_max_lifetime_minutes=720,
            ),
            None,
            None,
        ),
    )

    # Act
    sync_okta_organization(
        neo4j_session,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "OKTA_ORG_ID": TEST_ORG_ID},
        okta_client,
    )

    # Assert
    assert check_nodes(
        neo4j_session,
        "OktaOrganization",
        [
            "id",
            "name",
            "admin_console_session_idle_timeout_minutes",
            "admin_console_session_max_lifetime_minutes",
        ],
    ) == {(TEST_ORG_ID, TEST_ORG_ID, 15, 720)}
