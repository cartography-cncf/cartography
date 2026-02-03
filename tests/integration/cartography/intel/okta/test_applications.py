from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.okta.applications
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ORG_ID = "test-okta-org-id"
TEST_UPDATE_TAG = 123456789


def _create_common_job_parameters():
    return {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "OKTA_ORG_ID": TEST_ORG_ID,
    }


def _create_mock_application(app_id: str, name: str, label: str) -> MagicMock:
    """Create a mock OktaApplication object with all required nested structures."""
    app = MagicMock()
    app.id = app_id
    app.name = name
    app.label = label
    app.created = "2019-01-01T00:00:01.000Z"
    app.last_updated = "2019-01-01T00:00:01.000Z"
    app.features = []

    # Status
    app.status = MagicMock()
    app.status.value = "ACTIVE"

    # Activated timestamp
    app.activated = "2019-01-01T00:00:01.000Z"

    # Sign on mode
    app.sign_on_mode = MagicMock()
    app.sign_on_mode.value = "SAML_2_0"

    # Licensing (optional - uses hasattr check)
    app.licensing = MagicMock()
    app.licensing.seat_count = None

    # Accessibility
    app.accessibility = MagicMock()
    app.accessibility.error_redirect_url = None
    app.accessibility.login_redirect_url = None
    app.accessibility.self_service = False

    # Credentials with nested signing and user_name_template
    app.credentials = MagicMock()
    app.credentials.signing = MagicMock()
    app.credentials.signing.kid = None
    app.credentials.signing.last_rotated = None
    app.credentials.signing.next_rotation = None
    app.credentials.signing.rotation_mode = None
    app.credentials.signing.use = None
    app.credentials.user_name_template = MagicMock()
    app.credentials.user_name_template.push_status = None
    app.credentials.user_name_template.suffix = None
    app.credentials.user_name_template.template = None
    app.credentials.user_name_template.type = None

    # Settings with deeply nested structures
    app.settings = MagicMock()
    app.settings.app = MagicMock()
    app.settings.app.acs_url = None
    app.settings.app.button_field = None
    app.settings.app.login_url_regex = None
    app.settings.app.org_name = None
    app.settings.app.password_field = None
    app.settings.app.url = None
    app.settings.app.username_field = None
    app.settings.implicit_assignment = False
    app.settings.inline_hook_id = None
    app.settings.notifications = MagicMock()
    app.settings.notifications.vpn = MagicMock()
    app.settings.notifications.vpn.help_url = None
    app.settings.notifications.vpn.message = None
    app.settings.notifications.vpn.network = MagicMock()
    app.settings.notifications.vpn.network.connection = None
    app.settings.notifications.vpn.network.exclude = []
    app.settings.notifications.vpn.network.include = []
    app.settings.notes = MagicMock()
    app.settings.notes.admin = None
    app.settings.notes.enduser = None
    # sign_on is optional (uses hasattr + None check for SAML apps)
    app.settings.sign_on = None
    # oauth_client is optional (uses hasattr + None check)
    app.settings.oauth_client = None

    # Visibility
    app.visibility = MagicMock()
    app.visibility.app_links = {}
    app.visibility.auto_launch = False
    app.visibility.auto_submit_toolbar = False
    app.visibility.hide = MagicMock()
    app.visibility.hide.as_dict = MagicMock(return_value={})

    return app


@patch.object(
    cartography.intel.okta.applications,
    "_get_okta_applications",
    new_callable=AsyncMock,
)
@patch.object(
    cartography.intel.okta.applications,
    "_get_application_assigned_users",
    new_callable=AsyncMock,
)
@patch.object(
    cartography.intel.okta.applications,
    "_get_application_assigned_groups",
    new_callable=AsyncMock,
)
def test_sync_okta_applications(
    mock_get_groups,
    mock_get_users,
    mock_get_apps,
    neo4j_session,
):
    """
    Test that Okta applications are synced correctly to the graph.
    """
    # Arrange - Create test applications
    test_app_1 = _create_mock_application("app-001", "salesforce", "Salesforce")
    test_app_2 = _create_mock_application("app-002", "github", "GitHub")

    # Mock the API calls
    mock_get_apps.return_value = [test_app_1, test_app_2]
    mock_get_users.return_value = []
    mock_get_groups.return_value = []

    # Create the OktaOrganization node first
    neo4j_session.run(
        """
        MERGE (o:OktaOrganization{id: $ORG_ID})
        ON CREATE SET o.firstseen = timestamp()
        SET o.lastupdated = $UPDATE_TAG
        """,
        ORG_ID=TEST_ORG_ID,
        UPDATE_TAG=TEST_UPDATE_TAG,
    )

    okta_client = MagicMock()
    common_job_parameters = _create_common_job_parameters()

    # Act - Call the main sync function
    cartography.intel.okta.applications.sync_okta_applications(
        okta_client,
        neo4j_session,
        common_job_parameters,
    )

    # Assert - Verify applications were created with correct properties
    expected_apps = {
        ("app-001", "salesforce", "Salesforce"),
        ("app-002", "github", "GitHub"),
    }
    actual_apps = check_nodes(neo4j_session, "OktaApplication", ["id", "name", "label"])
    assert actual_apps == expected_apps

    # Assert - Verify applications are connected to organization
    expected_org_rels = {
        (TEST_ORG_ID, "app-001"),
        (TEST_ORG_ID, "app-002"),
    }
    actual_org_rels = check_rels(
        neo4j_session,
        "OktaOrganization",
        "id",
        "OktaApplication",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    )
    assert actual_org_rels == expected_org_rels


@patch.object(
    cartography.intel.okta.applications,
    "_get_okta_applications",
    new_callable=AsyncMock,
)
@patch.object(
    cartography.intel.okta.applications,
    "_get_application_assigned_users",
    new_callable=AsyncMock,
)
@patch.object(
    cartography.intel.okta.applications,
    "_get_application_assigned_groups",
    new_callable=AsyncMock,
)
def test_sync_okta_applications_with_users(
    mock_get_groups,
    mock_get_users,
    mock_get_apps,
    neo4j_session,
):
    """
    Test that application-to-user relationships are created correctly.
    """
    # Arrange - Create test application
    test_app = _create_mock_application("app-with-users", "test_app", "Test App")

    # Create test users in the graph first
    neo4j_session.run(
        """
        MERGE (o:OktaOrganization{id: $ORG_ID})
        SET o.lastupdated = $UPDATE_TAG
        MERGE (o)-[:RESOURCE]->(u1:OktaUser{id: 'user-001'})
        SET u1.email = 'user1@example.com', u1.lastupdated = $UPDATE_TAG
        MERGE (o)-[:RESOURCE]->(u2:OktaUser{id: 'user-002'})
        SET u2.email = 'user2@example.com', u2.lastupdated = $UPDATE_TAG
        """,
        ORG_ID=TEST_ORG_ID,
        UPDATE_TAG=TEST_UPDATE_TAG,
    )

    # Mock the API calls
    # _get_application_assigned_users returns a list of user ID strings
    mock_get_apps.return_value = [test_app]
    mock_get_users.return_value = ["user-001", "user-002"]
    mock_get_groups.return_value = []

    okta_client = MagicMock()
    common_job_parameters = _create_common_job_parameters()

    # Act
    cartography.intel.okta.applications.sync_okta_applications(
        okta_client,
        neo4j_session,
        common_job_parameters,
    )

    # Assert - Verify APPLICATION relationships between users and application
    expected_user_app_rels = {
        ("user-001", "app-with-users"),
        ("user-002", "app-with-users"),
    }
    actual_user_app_rels = check_rels(
        neo4j_session,
        "OktaUser",
        "id",
        "OktaApplication",
        "id",
        "APPLICATION",
        rel_direction_right=True,
    )
    assert actual_user_app_rels == expected_user_app_rels


@patch.object(
    cartography.intel.okta.applications,
    "_get_okta_applications",
    new_callable=AsyncMock,
)
@patch.object(
    cartography.intel.okta.applications,
    "_get_application_assigned_users",
    new_callable=AsyncMock,
)
@patch.object(
    cartography.intel.okta.applications,
    "_get_application_assigned_groups",
    new_callable=AsyncMock,
)
def test_sync_okta_applications_with_groups(
    mock_get_groups,
    mock_get_users,
    mock_get_apps,
    neo4j_session,
):
    """
    Test that application-to-group relationships are created correctly.
    """
    # Arrange - Create test application
    test_app = _create_mock_application("app-with-groups", "test_app", "Test App")

    # Create test groups in the graph first
    neo4j_session.run(
        """
        MERGE (o:OktaOrganization{id: $ORG_ID})
        SET o.lastupdated = $UPDATE_TAG
        MERGE (o)-[:RESOURCE]->(g1:OktaGroup{id: 'group-001'})
        SET g1.name = 'Engineering', g1.lastupdated = $UPDATE_TAG
        MERGE (o)-[:RESOURCE]->(g2:OktaGroup{id: 'group-002'})
        SET g2.name = 'Product', g2.lastupdated = $UPDATE_TAG
        """,
        ORG_ID=TEST_ORG_ID,
        UPDATE_TAG=TEST_UPDATE_TAG,
    )

    # Mock the API calls
    # _get_application_assigned_groups returns a list of group ID strings
    mock_get_apps.return_value = [test_app]
    mock_get_users.return_value = []
    mock_get_groups.return_value = ["group-001", "group-002"]

    okta_client = MagicMock()
    common_job_parameters = _create_common_job_parameters()

    # Act
    cartography.intel.okta.applications.sync_okta_applications(
        okta_client,
        neo4j_session,
        common_job_parameters,
    )

    # Assert - Verify APPLICATION relationships between groups and application
    expected_group_app_rels = {
        ("group-001", "app-with-groups"),
        ("group-002", "app-with-groups"),
    }
    actual_group_app_rels = check_rels(
        neo4j_session,
        "OktaGroup",
        "id",
        "OktaApplication",
        "id",
        "APPLICATION",
        rel_direction_right=True,
    )
    assert actual_group_app_rels == expected_group_app_rels


@patch.object(
    cartography.intel.okta.applications,
    "_get_okta_applications",
    new_callable=AsyncMock,
)
@patch.object(
    cartography.intel.okta.applications,
    "_get_application_assigned_users",
    new_callable=AsyncMock,
)
@patch.object(
    cartography.intel.okta.applications,
    "_get_application_assigned_groups",
    new_callable=AsyncMock,
)
def test_sync_okta_applications_updates_existing(
    mock_get_groups,
    mock_get_users,
    mock_get_apps,
    neo4j_session,
):
    """
    Test that syncing updates existing applications rather than creating duplicates.
    """
    # Arrange - Create an existing application in the graph
    neo4j_session.run(
        """
        MERGE (o:OktaOrganization{id: $ORG_ID})
        SET o.lastupdated = $UPDATE_TAG
        MERGE (o)-[:RESOURCE]->(app:OktaApplication{id: 'app-existing'})
        SET app.name = 'old_name',
            app.label = 'Old Label',
            app.status = 'INACTIVE',
            app.lastupdated = 111111
        """,
        ORG_ID=TEST_ORG_ID,
        UPDATE_TAG=TEST_UPDATE_TAG,
    )

    # Create updated application data
    test_app = _create_mock_application("app-existing", "updated_name", "Updated Label")

    mock_get_apps.return_value = [test_app]
    mock_get_users.return_value = []
    mock_get_groups.return_value = []

    okta_client = MagicMock()
    common_job_parameters = _create_common_job_parameters()

    # Act
    cartography.intel.okta.applications.sync_okta_applications(
        okta_client,
        neo4j_session,
        common_job_parameters,
    )

    # Assert - Application should be updated, not duplicated
    result = neo4j_session.run(
        """
        MATCH (app:OktaApplication{id: 'app-existing'})
        RETURN app.name as name, app.label as label, app.status as status, app.lastupdated as lastupdated
        """,
    )
    apps = [dict(r) for r in result]
    assert len(apps) == 1  # Should be only one application
    app_data = apps[0]
    assert app_data["name"] == "updated_name"
    assert app_data["label"] == "Updated Label"
    assert app_data["status"] == "ACTIVE"
    assert app_data["lastupdated"] == TEST_UPDATE_TAG
