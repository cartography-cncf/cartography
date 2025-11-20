from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.okta.applications
from tests.data.okta.application import create_test_application
from tests.data.okta.application import LIST_APPLICATION_GROUP_ASSIGNED_RESPONSE
from tests.data.okta.application import LIST_APPLICATION_USER_ASSIGNED_RESPONSE
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ORG_ID = "test-okta-org-id"
TEST_UPDATE_TAG = 123456789
TEST_API_KEY = "test-api-key"


@patch.object(cartography.intel.okta.applications, "create_api_client")
@patch.object(cartography.intel.okta.applications, "_get_okta_applications")
@patch.object(cartography.intel.okta.applications, "_get_application_assigned_users")
@patch.object(cartography.intel.okta.applications, "_get_application_assigned_groups")
def test_sync_okta_applications(
    mock_get_groups,
    mock_get_users,
    mock_get_apps,
    mock_api_client,
    neo4j_session,
):
    """
    Test that Okta applications are synced correctly to the graph.
    This follows the recommended pattern: mock get() functions, call sync(), verify outcomes.
    """
    # Arrange - Create test applications
    test_app_1 = create_test_application()
    test_app_1["id"] = "app-001"
    test_app_1["name"] = "salesforce"
    test_app_1["label"] = "Salesforce"
    test_app_1["settings"] = {}  # Add settings key to avoid KeyError

    test_app_2 = create_test_application()
    test_app_2["id"] = "app-002"
    test_app_2["name"] = "github"
    test_app_2["label"] = "GitHub"
    test_app_2["settings"] = {}  # Add settings key to avoid KeyError

    # Mock the API calls
    mock_get_apps.return_value = [test_app_1, test_app_2]
    mock_get_users.return_value = []
    mock_get_groups.return_value = []
    mock_api_client.return_value = MagicMock()

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

    # Act - Call the main sync function
    cartography.intel.okta.applications.sync_okta_applications(
        neo4j_session,
        TEST_ORG_ID,
        TEST_UPDATE_TAG,
        TEST_API_KEY,
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


@patch.object(cartography.intel.okta.applications, "create_api_client")
@patch.object(cartography.intel.okta.applications, "_get_okta_applications")
@patch.object(cartography.intel.okta.applications, "_get_application_assigned_users")
@patch.object(cartography.intel.okta.applications, "_get_application_assigned_groups")
def test_sync_okta_applications_with_users(
    mock_get_groups,
    mock_get_users,
    mock_get_apps,
    mock_api_client,
    neo4j_session,
):
    """
    Test that application-to-user relationships are created correctly.
    """
    # Arrange - Create test application
    test_app = create_test_application()
    test_app["id"] = "app-with-users"
    test_app["name"] = "test_app"
    test_app["settings"] = {}  # Add settings key

    # Create test users in the graph first
    neo4j_session.run(
        """
        MERGE (o:OktaOrganization{id: $ORG_ID})
        SET o.lastupdated = $UPDATE_TAG
        MERGE (o)-[:RESOURCE]->(u1:OktaUser{id: '00ui2sVIFZNCNKFFNBPM'})
        SET u1.email = 'user1@example.com', u1.lastupdated = $UPDATE_TAG
        MERGE (o)-[:RESOURCE]->(u2:OktaUser{id: '00ujsgVNDRESKKXERBUJ'})
        SET u2.email = 'user2@example.com', u2.lastupdated = $UPDATE_TAG
        """,
        ORG_ID=TEST_ORG_ID,
        UPDATE_TAG=TEST_UPDATE_TAG,
    )

    # Mock the API calls
    mock_get_apps.return_value = [test_app]
    mock_get_users.return_value = [LIST_APPLICATION_USER_ASSIGNED_RESPONSE]
    mock_get_groups.return_value = []
    mock_api_client.return_value = MagicMock()

    # Act
    cartography.intel.okta.applications.sync_okta_applications(
        neo4j_session,
        TEST_ORG_ID,
        TEST_UPDATE_TAG,
        TEST_API_KEY,
    )

    # Assert - Verify APPLICATION relationships between users and application
    expected_user_app_rels = {
        ("00ui2sVIFZNCNKFFNBPM", "app-with-users"),
        ("00ujsgVNDRESKKXERBUJ", "app-with-users"),
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


@patch.object(cartography.intel.okta.applications, "create_api_client")
@patch.object(cartography.intel.okta.applications, "_get_okta_applications")
@patch.object(cartography.intel.okta.applications, "_get_application_assigned_users")
@patch.object(cartography.intel.okta.applications, "_get_application_assigned_groups")
def test_sync_okta_applications_with_groups(
    mock_get_groups,
    mock_get_users,
    mock_get_apps,
    mock_api_client,
    neo4j_session,
):
    """
    Test that application-to-group relationships are created correctly.
    """
    # Arrange - Create test application
    test_app = create_test_application()
    test_app["id"] = "app-with-groups"
    test_app["name"] = "test_app"
    test_app["settings"] = {}  # Add settings key

    # Create test groups in the graph first
    neo4j_session.run(
        """
        MERGE (o:OktaOrganization{id: $ORG_ID})
        SET o.lastupdated = $UPDATE_TAG
        MERGE (o)-[:RESOURCE]->(g1:OktaGroup{id: '00gbkkGFFWZDLCNTAGQR'})
        SET g1.name = 'Engineering', g1.lastupdated = $UPDATE_TAG
        MERGE (o)-[:RESOURCE]->(g2:OktaGroup{id: '00gg0xVALADWBPXOFZAS'})
        SET g2.name = 'Product', g2.lastupdated = $UPDATE_TAG
        """,
        ORG_ID=TEST_ORG_ID,
        UPDATE_TAG=TEST_UPDATE_TAG,
    )

    # Mock the API calls
    mock_get_apps.return_value = [test_app]
    mock_get_users.return_value = []
    mock_get_groups.return_value = [LIST_APPLICATION_GROUP_ASSIGNED_RESPONSE]
    mock_api_client.return_value = MagicMock()

    # Act
    cartography.intel.okta.applications.sync_okta_applications(
        neo4j_session,
        TEST_ORG_ID,
        TEST_UPDATE_TAG,
        TEST_API_KEY,
    )

    # Assert - Verify APPLICATION relationships between groups and application
    expected_group_app_rels = {
        ("00gbkkGFFWZDLCNTAGQR", "app-with-groups"),
        ("00gg0xVALADWBPXOFZAS", "app-with-groups"),
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


@patch.object(cartography.intel.okta.applications, "create_api_client")
@patch.object(cartography.intel.okta.applications, "_get_okta_applications")
@patch.object(cartography.intel.okta.applications, "_get_application_assigned_users")
@patch.object(cartography.intel.okta.applications, "_get_application_assigned_groups")
def test_sync_okta_applications_with_reply_urls(
    mock_get_groups,
    mock_get_users,
    mock_get_apps,
    mock_api_client,
    neo4j_session,
):
    """
    Test that reply URLs are created and linked to applications correctly.
    """
    # Arrange - Create test application with redirect URIs
    test_app = {
        "id": "app-with-redirects",
        "name": "oauth_app",
        "label": "OAuth App",
        "created": "2019-01-01T00:00:01.000Z",
        "lastUpdated": "2019-01-01T00:00:01.000Z",
        "status": "ACTIVE",
        "activated": "2019-01-01T00:00:01.000Z",
        "features": [],
        "signOnMode": "OPENID_CONNECT",
        "settings": {
            "oauthClient": {
                "redirect_uris": [
                    "https://example.com/callback1",
                    "https://example.com/callback2",
                ],
            },
        },
    }

    # Create organization
    neo4j_session.run(
        """
        MERGE (o:OktaOrganization{id: $ORG_ID})
        SET o.lastupdated = $UPDATE_TAG
        """,
        ORG_ID=TEST_ORG_ID,
        UPDATE_TAG=TEST_UPDATE_TAG,
    )

    # Mock the API calls
    mock_get_apps.return_value = [test_app]
    mock_get_users.return_value = []
    mock_get_groups.return_value = []
    mock_api_client.return_value = MagicMock()

    # Act
    cartography.intel.okta.applications.sync_okta_applications(
        neo4j_session,
        TEST_ORG_ID,
        TEST_UPDATE_TAG,
        TEST_API_KEY,
    )

    # Assert - Verify ReplyUri nodes were created
    expected_uris = {
        ("https://example.com/callback1",),
        ("https://example.com/callback2",),
    }
    actual_uris = check_nodes(neo4j_session, "ReplyUri", ["uri"])
    assert actual_uris == expected_uris

    # Assert - Verify REPLYURI relationships
    expected_uri_rels = {
        ("app-with-redirects", "https://example.com/callback1"),
        ("app-with-redirects", "https://example.com/callback2"),
    }
    actual_uri_rels = check_rels(
        neo4j_session,
        "OktaApplication",
        "id",
        "ReplyUri",
        "uri",
        "REPLYURI",
        rel_direction_right=True,
    )
    assert actual_uri_rels == expected_uri_rels


@patch.object(cartography.intel.okta.applications, "create_api_client")
@patch.object(cartography.intel.okta.applications, "_get_okta_applications")
@patch.object(cartography.intel.okta.applications, "_get_application_assigned_users")
@patch.object(cartography.intel.okta.applications, "_get_application_assigned_groups")
def test_sync_okta_applications_updates_existing(
    mock_get_groups,
    mock_get_users,
    mock_get_apps,
    mock_api_client,
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
    test_app = create_test_application()
    test_app["id"] = "app-existing"
    test_app["name"] = "updated_name"
    test_app["label"] = "Updated Label"
    test_app["status"] = "ACTIVE"
    test_app["settings"] = {}  # Add settings key

    mock_get_apps.return_value = [test_app]
    mock_get_users.return_value = []
    mock_get_groups.return_value = []
    mock_api_client.return_value = MagicMock()

    # Act
    cartography.intel.okta.applications.sync_okta_applications(
        neo4j_session,
        TEST_ORG_ID,
        TEST_UPDATE_TAG,
        TEST_API_KEY,
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
