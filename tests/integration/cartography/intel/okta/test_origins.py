from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.okta.origins
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ORG_ID = "test-okta-org-id"
TEST_UPDATE_TAG = 123456789


def _create_common_job_parameters():
    return {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "OKTA_ORG_ID": TEST_ORG_ID,
    }


def _create_test_origin(
    origin_id: str,
    name: str,
    origin_url: str,
    status: str = "ACTIVE",
    cors: bool = False,
    redirect: bool = False,
    iframe: bool = False,
):
    """Create a mock TrustedOrigin object."""
    origin = MagicMock()
    origin.id = origin_id
    origin.name = name
    origin.origin = origin_url
    origin.status = status
    origin.created = "2019-01-01T00:00:01.000Z"
    origin.created_by = "admin-001"
    origin.last_updated = "2019-01-01T00:00:01.000Z"
    origin.last_updated_by = "admin-001"

    # Setup scopes
    scopes = []
    if cors:
        cors_scope = MagicMock()
        cors_scope.type = MagicMock()
        cors_scope.type.value = "CORS"
        cors_scope.allowed_okta_apps = []
        scopes.append(cors_scope)
    if redirect:
        redirect_scope = MagicMock()
        redirect_scope.type = MagicMock()
        redirect_scope.type.value = "REDIRECT"
        redirect_scope.allowed_okta_apps = []
        scopes.append(redirect_scope)
    if iframe:
        iframe_scope = MagicMock()
        iframe_scope.type = MagicMock()
        iframe_scope.type.value = "IFRAME_EMBED"
        iframe_scope.allowed_okta_apps = []
        scopes.append(iframe_scope)

    origin.scopes = scopes
    return origin


@patch.object(
    cartography.intel.okta.origins, "_get_okta_origins", new_callable=AsyncMock
)
def test_sync_okta_origins(mock_get_origins, neo4j_session):
    """
    Test that Okta trusted origins are synced correctly to the graph.
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

    # Create test origins
    origin_1 = _create_test_origin(
        "origin-001",
        "Example Origin",
        "https://example.com",
        cors=True,
    )
    origin_2 = _create_test_origin(
        "origin-002",
        "Another Origin",
        "https://another.example.com",
        redirect=True,
    )

    # Mock the API calls
    mock_get_origins.return_value = [origin_1, origin_2]

    okta_client = MagicMock()
    common_job_parameters = _create_common_job_parameters()

    # Act - Call the main sync function
    cartography.intel.okta.origins.sync_okta_origins(
        okta_client,
        neo4j_session,
        common_job_parameters,
    )

    # Assert - Verify trusted origins were created with correct properties
    expected_origins = {
        ("origin-001", "Example Origin", "https://example.com", "ACTIVE"),
        ("origin-002", "Another Origin", "https://another.example.com", "ACTIVE"),
    }
    actual_origins = check_nodes(
        neo4j_session, "OktaTrustedOrigin", ["id", "name", "origin", "status"]
    )
    assert actual_origins == expected_origins

    # Assert - Verify origins are connected to organization
    expected_org_rels = {
        (TEST_ORG_ID, "origin-001"),
        (TEST_ORG_ID, "origin-002"),
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


@patch.object(
    cartography.intel.okta.origins, "_get_okta_origins", new_callable=AsyncMock
)
def test_sync_okta_origins_with_no_origins(mock_get_origins, neo4j_session):
    """
    Test that sync handles gracefully when there are no trusted origins.
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
    mock_get_origins.return_value = []

    okta_client = MagicMock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "OKTA_ORG_ID": test_org_id,
    }

    # Act - Should not crash
    cartography.intel.okta.origins.sync_okta_origins(
        okta_client,
        neo4j_session,
        common_job_parameters,
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


@patch.object(
    cartography.intel.okta.origins, "_get_okta_origins", new_callable=AsyncMock
)
def test_sync_okta_origins_updates_existing(mock_get_origins, neo4j_session):
    """
    Test that syncing updates existing trusted origins rather than creating duplicates.
    """
    # Arrange - Create an existing trusted origin
    neo4j_session.run(
        """
        MERGE (o:OktaOrganization{id: $ORG_ID})
        SET o.lastupdated = $UPDATE_TAG
        MERGE (o)-[:RESOURCE]->(origin:OktaTrustedOrigin{id: 'origin-existing'})
        SET origin.name = 'Old Name',
            origin.origin = 'https://old-example.com',
            origin.status = 'INACTIVE',
            origin.lastupdated = 111111
        """,
        ORG_ID=TEST_ORG_ID,
        UPDATE_TAG=TEST_UPDATE_TAG,
    )

    # Create updated origin
    updated_origin = _create_test_origin(
        "origin-existing",
        "Updated Name",
        "https://updated-example.com",
        status="ACTIVE",
        cors=True,
    )

    # Mock API with updated data
    mock_get_origins.return_value = [updated_origin]

    okta_client = MagicMock()
    common_job_parameters = _create_common_job_parameters()

    # Act
    cartography.intel.okta.origins.sync_okta_origins(
        okta_client,
        neo4j_session,
        common_job_parameters,
    )

    # Assert - Origin should be updated, not duplicated
    result = neo4j_session.run(
        """
        MATCH (origin:OktaTrustedOrigin{id: 'origin-existing'})
        RETURN origin.name as name, origin.origin as origin, origin.status as status, origin.lastupdated as lastupdated
        """,
    )
    origins = [dict(r) for r in result]
    assert len(origins) == 1  # Should be only one origin
    origin_data = origins[0]
    assert origin_data["name"] == "Updated Name"
    assert origin_data["origin"] == "https://updated-example.com"
    assert origin_data["status"] == "ACTIVE"
    assert origin_data["lastupdated"] == TEST_UPDATE_TAG


@patch.object(
    cartography.intel.okta.origins, "_get_okta_origins", new_callable=AsyncMock
)
def test_sync_okta_origins_with_different_scopes(mock_get_origins, neo4j_session):
    """
    Test that origins with different scope types (CORS, REDIRECT, IFRAME) are handled correctly.
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

    # Create test origins with various scope combinations
    cors_origin = _create_test_origin(
        "cors-only",
        "CORS Only Origin",
        "https://cors.example.com",
        cors=True,
    )
    redirect_origin = _create_test_origin(
        "redirect-only",
        "Redirect Only Origin",
        "https://redirect.example.com",
        redirect=True,
    )
    both_origin = _create_test_origin(
        "both-scopes",
        "Both Scopes Origin",
        "https://both.example.com",
        cors=True,
        redirect=True,
    )

    mock_get_origins.return_value = [cors_origin, redirect_origin, both_origin]

    okta_client = MagicMock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "OKTA_ORG_ID": test_org_id,
    }

    # Act
    cartography.intel.okta.origins.sync_okta_origins(
        okta_client,
        neo4j_session,
        common_job_parameters,
    )

    # Assert - All three origins should be created for this org
    result = neo4j_session.run(
        """
        MATCH (org:OktaOrganization{id: $ORG_ID})-[:RESOURCE]->(o:OktaTrustedOrigin)
        RETURN o.id as id, o.name as name, o.cors_allowed as cors_allowed, o.redirect_allowed as redirect_allowed
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

    # Verify scope-specific properties
    result = neo4j_session.run(
        """
        MATCH (o:OktaTrustedOrigin{id: 'both-scopes'})
        RETURN o.cors_allowed as cors_allowed, o.redirect_allowed as redirect_allowed
        """,
    )
    scope_data = [dict(r) for r in result][0]
    assert scope_data["cors_allowed"] is True
    assert scope_data["redirect_allowed"] is True


@patch.object(
    cartography.intel.okta.origins, "_get_okta_origins", new_callable=AsyncMock
)
def test_sync_okta_origins_with_inactive_status(mock_get_origins, neo4j_session):
    """
    Test that inactive trusted origins are synced correctly.
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

    inactive_origin = _create_test_origin(
        "inactive-origin",
        "Inactive Origin",
        "https://inactive.example.com",
        status="INACTIVE",
        cors=True,
    )

    mock_get_origins.return_value = [inactive_origin]

    okta_client = MagicMock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "OKTA_ORG_ID": test_org_id,
    }

    # Act
    cartography.intel.okta.origins.sync_okta_origins(
        okta_client,
        neo4j_session,
        common_job_parameters,
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
