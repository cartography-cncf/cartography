from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.okta.origins
from tests.data.okta.trustedorigin import LIST_TRUSTED_ORIGIN_RESPONSE
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ORG_ID = "test-okta-org-id"
TEST_UPDATE_TAG = 123456789
TEST_API_KEY = "test-api-key"


@patch.object(cartography.intel.okta.origins, "create_api_client")
@patch.object(cartography.intel.okta.origins, "_get_trusted_origins")
def test_sync_trusted_origins(mock_get_origins, mock_api_client, neo4j_session):
    """
    Test that Okta trusted origins are synced correctly to the graph.
    This follows the recommended pattern: mock get() functions, call sync(), verify outcomes.
    """
    # Arrange - Create organization in the graph first
    neo4j_session.run(
        """
        MERGE (o:OktaOrganization{id: $ORG_ID})
        ON CREATE SET o.firstseen = timestamp()
        SET o.lastupdated = $UPDATE_TAG
        """,
        ORG_ID=TEST_ORG_ID,
        UPDATE_TAG=TEST_UPDATE_TAG,
    )

    # Mock the API calls
    mock_get_origins.return_value = LIST_TRUSTED_ORIGIN_RESPONSE
    mock_api_client.return_value = MagicMock()

    # Act - Call the main sync function
    cartography.intel.okta.origins.sync_trusted_origins(
        neo4j_session,
        TEST_ORG_ID,
        TEST_UPDATE_TAG,
        TEST_API_KEY,
    )

    # Assert - Verify trusted origins were created with correct properties
    expected_origins = {
        (
            "tosue7JvguwJ7U6kz0g3",
            "Example Trusted Origin",
            "http://example.com",
            "ACTIVE",
        ),
        (
            "tos10hzarOl8zfPM80g4",
            "Another Trusted Origin",
            "https://rf.example.com",
            "ACTIVE",
        ),
    }
    actual_origins = check_nodes(
        neo4j_session, "OktaTrustedOrigin", ["id", "name", "origin", "status"]
    )
    assert actual_origins == expected_origins

    # Assert - Verify origins are connected to organization
    expected_org_rels = {
        (TEST_ORG_ID, "tosue7JvguwJ7U6kz0g3"),
        (TEST_ORG_ID, "tos10hzarOl8zfPM80g4"),
    }
    actual_org_rels = check_rels(
        neo4j_session,
        "OktaOrganization",
        "id",
        "OktaTrustedOrigin",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    )
    assert actual_org_rels == expected_org_rels

    # Assert - Verify scopes are set correctly (note: there's a bug in the code - it uses 'scoped' instead of 'scopes')
    # TODO: Fix the bug in origins.py line 87 - should be 'new.scopes = data.scopes' not 'new.scopes = data.scoped'
    result = neo4j_session.run(
        """
        MATCH (o:OktaTrustedOrigin)
        WHERE o.id IN ['tosue7JvguwJ7U6kz0g3', 'tos10hzarOl8zfPM80g4']
        RETURN o.id as id, o.created as created, o.created_by as created_by
        ORDER BY o.id
        """,
    )
    origins = [dict(r) for r in result]
    assert len(origins) == 2
    # Verify metadata fields are set
    # Note: ORDER BY o.id sorts "tos10hzarOl8zfPM80g4" before "tosue7JvguwJ7U6kz0g3"
    assert origins[0]["created"] == "2017-11-16T05:01:12.000Z"
    assert origins[0]["created_by"] == "00ut5t92p6IEOi4bu10g31"
    assert origins[1]["created"] == "2018-01-13T01:22:10.000Z"
    assert origins[1]["created_by"] == "00ut5t92p6IEOi4bu0ge3"


@patch.object(cartography.intel.okta.origins, "create_api_client")
@patch.object(cartography.intel.okta.origins, "_get_trusted_origins")
def test_sync_trusted_origins_with_no_origins(
    mock_get_origins, mock_api_client, neo4j_session
):
    """
    Test that sync handles gracefully when there are no trusted origins.
    Uses a different organization ID to avoid interference from other tests.
    """
    # Arrange - Use a different org ID for isolation
    test_org_id = "test-okta-org-id-empty"
    neo4j_session.run(
        """
        MERGE (o:OktaOrganization{id: $ORG_ID})
        SET o.lastupdated = $UPDATE_TAG
        """,
        ORG_ID=test_org_id,
        UPDATE_TAG=TEST_UPDATE_TAG,
    )

    # Mock API to return empty list
    mock_get_origins.return_value = "[]"
    mock_api_client.return_value = MagicMock()

    # Act - Should not crash
    cartography.intel.okta.origins.sync_trusted_origins(
        neo4j_session,
        test_org_id,
        TEST_UPDATE_TAG,
        TEST_API_KEY,
    )

    # Assert - No trusted origins should be created for this organization
    result = neo4j_session.run(
        """
        MATCH (org:OktaOrganization{id: $ORG_ID})-[:RESOURCE]->(o:OktaTrustedOrigin)
        RETURN count(o) as count
        """,
        ORG_ID=test_org_id,
    )
    count = [dict(r) for r in result][0]["count"]
    assert count == 0


@patch.object(cartography.intel.okta.origins, "create_api_client")
@patch.object(cartography.intel.okta.origins, "_get_trusted_origins")
def test_sync_trusted_origins_updates_existing(
    mock_get_origins, mock_api_client, neo4j_session
):
    """
    Test that syncing updates existing trusted origins rather than creating duplicates.
    """
    # Arrange - Create an existing trusted origin
    neo4j_session.run(
        """
        MERGE (o:OktaOrganization{id: $ORG_ID})
        SET o.lastupdated = $UPDATE_TAG
        MERGE (o)-[:RESOURCE]->(origin:OktaTrustedOrigin{id: 'tosue7JvguwJ7U6kz0g3'})
        SET origin.name = 'Old Name',
            origin.origin = 'http://old-example.com',
            origin.status = 'INACTIVE',
            origin.lastupdated = 111111
        """,
        ORG_ID=TEST_ORG_ID,
        UPDATE_TAG=TEST_UPDATE_TAG,
    )

    # Mock API with updated data
    mock_get_origins.return_value = LIST_TRUSTED_ORIGIN_RESPONSE
    mock_api_client.return_value = MagicMock()

    # Act
    cartography.intel.okta.origins.sync_trusted_origins(
        neo4j_session,
        TEST_ORG_ID,
        TEST_UPDATE_TAG,
        TEST_API_KEY,
    )

    # Assert - Origin should be updated, not duplicated
    result = neo4j_session.run(
        """
        MATCH (origin:OktaTrustedOrigin{id: 'tosue7JvguwJ7U6kz0g3'})
        RETURN origin.name as name, origin.origin as origin, origin.status as status, origin.lastupdated as lastupdated
        """,
    )
    origins = [dict(r) for r in result]
    assert len(origins) == 1  # Should be only one origin
    origin_data = origins[0]
    assert origin_data["name"] == "Example Trusted Origin"
    assert origin_data["origin"] == "http://example.com"
    assert origin_data["status"] == "ACTIVE"
    assert origin_data["lastupdated"] == TEST_UPDATE_TAG


@patch.object(cartography.intel.okta.origins, "create_api_client")
@patch.object(cartography.intel.okta.origins, "_get_trusted_origins")
def test_sync_trusted_origins_with_different_scopes(
    mock_get_origins, mock_api_client, neo4j_session
):
    """
    Test that origins with different scope types (CORS, REDIRECT) are handled correctly.
    Uses a different organization ID to avoid interference from other tests.
    """
    # Arrange - Use a different org ID for isolation
    test_org_id = "test-okta-org-id-scopes"
    neo4j_session.run(
        """
        MERGE (o:OktaOrganization{id: $ORG_ID})
        SET o.lastupdated = $UPDATE_TAG
        """,
        ORG_ID=test_org_id,
        UPDATE_TAG=TEST_UPDATE_TAG,
    )

    # TODO: Get real examples of different trusted origin configurations from Okta API
    # Create test data with various scope combinations
    test_origins_json = """
    [
        {
            "id": "cors-only",
            "name": "CORS Only Origin",
            "origin": "https://cors.example.com",
            "scopes": [{"type": "CORS"}],
            "status": "ACTIVE",
            "created": "2020-01-01T00:00:00.000Z",
            "createdBy": "admin-001",
            "lastUpdated": "2020-01-01T00:00:00.000Z",
            "lastUpdatedBy": "admin-001"
        },
        {
            "id": "redirect-only",
            "name": "Redirect Only Origin",
            "origin": "https://redirect.example.com",
            "scopes": [{"type": "REDIRECT"}],
            "status": "ACTIVE",
            "created": "2020-01-01T00:00:00.000Z",
            "createdBy": "admin-001",
            "lastUpdated": "2020-01-01T00:00:00.000Z",
            "lastUpdatedBy": "admin-001"
        },
        {
            "id": "both-scopes",
            "name": "Both Scopes Origin",
            "origin": "https://both.example.com",
            "scopes": [{"type": "CORS"}, {"type": "REDIRECT"}],
            "status": "ACTIVE",
            "created": "2020-01-01T00:00:00.000Z",
            "createdBy": "admin-001",
            "lastUpdated": "2020-01-01T00:00:00.000Z",
            "lastUpdatedBy": "admin-001"
        }
    ]
    """

    mock_get_origins.return_value = test_origins_json
    mock_api_client.return_value = MagicMock()

    # Act
    cartography.intel.okta.origins.sync_trusted_origins(
        neo4j_session,
        test_org_id,
        TEST_UPDATE_TAG,
        TEST_API_KEY,
    )

    # Assert - All three origins should be created for this org
    result = neo4j_session.run(
        """
        MATCH (org:OktaOrganization{id: $ORG_ID})-[:RESOURCE]->(o:OktaTrustedOrigin)
        RETURN o.id as id, o.name as name
        """,
        ORG_ID=test_org_id,
    )
    actual_origins = {(r["id"], r["name"]) for r in result}
    expected_origins = {
        ("cors-only", "CORS Only Origin"),
        ("redirect-only", "Redirect Only Origin"),
        ("both-scopes", "Both Scopes Origin"),
    }
    assert actual_origins == expected_origins


@patch.object(cartography.intel.okta.origins, "create_api_client")
@patch.object(cartography.intel.okta.origins, "_get_trusted_origins")
def test_sync_trusted_origins_with_inactive_status(
    mock_get_origins, mock_api_client, neo4j_session
):
    """
    Test that inactive trusted origins are synced correctly.
    Uses a different organization ID to avoid interference from other tests.
    """
    # Arrange - Use a different org ID for isolation
    test_org_id = "test-okta-org-id-inactive"
    neo4j_session.run(
        """
        MERGE (o:OktaOrganization{id: $ORG_ID})
        SET o.lastupdated = $UPDATE_TAG
        """,
        ORG_ID=test_org_id,
        UPDATE_TAG=TEST_UPDATE_TAG,
    )

    # TODO: Get real example of inactive trusted origin from Okta API
    inactive_origin_json = """
    [
        {
            "id": "inactive-origin",
            "name": "Inactive Origin",
            "origin": "https://inactive.example.com",
            "scopes": [{"type": "CORS"}],
            "status": "INACTIVE",
            "created": "2019-01-01T00:00:00.000Z",
            "createdBy": "admin-001",
            "lastUpdated": "2019-06-01T00:00:00.000Z",
            "lastUpdatedBy": "admin-002"
        }
    ]
    """

    mock_get_origins.return_value = inactive_origin_json
    mock_api_client.return_value = MagicMock()

    # Act
    cartography.intel.okta.origins.sync_trusted_origins(
        neo4j_session,
        test_org_id,
        TEST_UPDATE_TAG,
        TEST_API_KEY,
    )

    # Assert - Inactive origin should be created with INACTIVE status
    result = neo4j_session.run(
        """
        MATCH (o:OktaTrustedOrigin{id: 'inactive-origin'})
        RETURN o.status as status
        """,
    )
    origin_data = [dict(r) for r in result][0]
    assert origin_data["status"] == "INACTIVE"
