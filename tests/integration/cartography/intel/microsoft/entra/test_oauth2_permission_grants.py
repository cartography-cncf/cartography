from unittest.mock import patch

import pytest
from msgraph.generated.models.o_auth2_permission_grant import OAuth2PermissionGrant

import cartography.intel.microsoft.entra.oauth2_permission_grants
from cartography.intel.microsoft.entra.oauth2_permission_grants import (
    MICROSOFT_GRAPH_APP_ID,
)
from cartography.intel.microsoft.entra.oauth2_permission_grants import (
    sync_oauth2_permission_grants,
)
from cartography.intel.microsoft.entra.users import load_tenant

TEST_TENANT_ID = "02b2b7cc-fb03-4324-bf6b-eb207b39c479"
TEST_UPDATE_TAG = 1234567890
STALE_UPDATE_TAG = TEST_UPDATE_TAG - 1

GRANTS = [
    OAuth2PermissionGrant(
        id="grant-1",
        client_id="sp-vendor",
        consent_type="Principal",
        principal_id="user-1",
        resource_id="sp-graph",
        scope="User.Read Mail.Read",
    ),
    OAuth2PermissionGrant(
        id="grant-2",
        client_id="sp-vendor",
        consent_type="AllPrincipals",
        resource_id="sp-graph",
        scope="User.Read",
    ),
]


async def _mock_get_oauth2_permission_grants(client):
    return list(GRANTS)


@patch.object(
    cartography.intel.microsoft.entra.oauth2_permission_grants,
    "get_oauth2_permission_grants",
    side_effect=_mock_get_oauth2_permission_grants,
)
@pytest.mark.asyncio
async def test_sync_oauth2_permission_grants(mock_get_grants, neo4j_session):
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    load_tenant(neo4j_session, {"id": TEST_TENANT_ID}, TEST_UPDATE_TAG)
    neo4j_session.run(
        """
        MATCH (t:AzureTenant {id: $tenant_id})
        CREATE (t)-[:RESOURCE]->(user1:EntraUser:UserAccount {id: 'user-1'})
        CREATE (t)-[:RESOURCE]->(user2:EntraUser:UserAccount {id: 'user-2'})
        CREATE (t)-[:RESOURCE]->(vendor:EntraServicePrincipal:ThirdPartyApp {id: 'sp-vendor'})
        CREATE (t)-[:RESOURCE]->(:EntraServicePrincipal {
            id: 'sp-graph', app_id: $graph_app_id
        })
        CREATE (t)-[:RESOURCE]->(revoked:EntraServicePrincipal:ThirdPartyApp {id: 'sp-revoked'})

        // The ontology job derived this edge from an app role assignment before the
        // user also consented; the grant takes it over.
        CREATE (user1)-[:AUTHORIZED {
            match_method: 'entra_app_role_assignment', lastupdated: $stale_tag
        }]->(vendor)

        // A consent revoked since the last sync.
        CREATE (user2)-[:AUTHORIZED {
            scopes: ['https://graph.microsoft.com/User.Read'],
            lastupdated: $stale_tag,
            _sub_resource_label: 'AzureTenant',
            _sub_resource_id: $tenant_id
        }]->(revoked)
        """,
        tenant_id=TEST_TENANT_ID,
        graph_app_id=MICROSOFT_GRAPH_APP_ID,
        stale_tag=STALE_UPDATE_TAG,
    )

    # Act
    await sync_oauth2_permission_grants(
        neo4j_session,
        TEST_TENANT_ID,
        "client-id",
        "client-secret",
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "TENANT_ID": TEST_TENANT_ID},
    )

    # Assert
    authorized = neo4j_session.run(
        """
        MATCH (u:EntraUser)-[r:AUTHORIZED]->(sp:EntraServicePrincipal)
        RETURN u.id AS user, sp.id AS app, r.scopes AS scopes, r.match_method AS method
        """
    ).data()
    assert authorized == [
        {
            "user": "user-1",
            "app": "sp-vendor",
            "scopes": [
                "https://graph.microsoft.com/Mail.Read",
                "https://graph.microsoft.com/User.Read",
            ],
            "method": None,
        },
    ]
    admin_consented = neo4j_session.run(
        """
        MATCH (:AzureTenant {id: $tenant_id})-[r:ADMIN_CONSENTED]->(sp:EntraServicePrincipal)
        RETURN sp.id AS app, r.scopes AS scopes
        """,
        tenant_id=TEST_TENANT_ID,
    ).data()
    assert admin_consented == [
        {"app": "sp-vendor", "scopes": ["https://graph.microsoft.com/User.Read"]},
    ]
