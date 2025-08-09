from unittest.mock import patch

import requests

import cartography.intel.keycloak.clients
import tests.data.keycloak.clients
from tests.integration.cartography.intel.keycloak.test_realms import (
    _ensure_local_neo4j_has_test_realms,
)
from tests.integration.cartography.intel.keycloak.test_scopes import (
    _ensure_local_neo4j_has_test_scopes,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_REALM = "simpson-corp"


def _ensure_local_neo4j_has_test_clients(neo4j_session):
    transformed_clients, service_accounts = (
        cartography.intel.keycloak.clients.transform(
            tests.data.keycloak.clients.KEYCLOAK_CLIENTS
        )
    )
    cartography.intel.keycloak.clients.load_service_accounts(
        neo4j_session,
        service_accounts,
        TEST_REALM,
        TEST_UPDATE_TAG,
    )
    cartography.intel.keycloak.clients.load_clients(
        neo4j_session,
        transformed_clients,
        TEST_REALM,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.keycloak.clients,
    "get",
    return_value=tests.data.keycloak.clients.KEYCLOAK_CLIENTS,
)
def test_load_keycloak_clients(mock_api, neo4j_session):
    # Arrange
    api_session = requests.Session()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "REALM": TEST_REALM,
    }
    _ensure_local_neo4j_has_test_realms(neo4j_session)
    _ensure_local_neo4j_has_test_scopes(neo4j_session)

    # Act
    cartography.intel.keycloak.clients.sync(
        neo4j_session,
        api_session,
        "",
        common_job_parameters,
    )

    # Assert Clients exist
    expected_nodes = [
        (c["id"], c.get("clientId"))
        for c in tests.data.keycloak.clients.KEYCLOAK_CLIENTS
    ]
    assert len(expected_nodes) > 0
    assert check_nodes(neo4j_session, "KeycloakClient", ["id", "client_id"]) == set(
        expected_nodes
    )

    # Assert Service Accounts exist
    expected_nodes = {
        ("1859462c-4b8d-4e8f-9084-a5494a4f0437", "service-account-burns-backdoor"),
    }
    assert (
        check_nodes(neo4j_session, "KeycloakUser", ["id", "username"]) == expected_nodes
    )

    # Assert Clients are connected with Realm
    expected_rels = [
        (c["id"], TEST_REALM) for c in tests.data.keycloak.clients.KEYCLOAK_CLIENTS
    ]
    assert len(expected_rels) > 0
    assert check_rels(
        neo4j_session,
        "KeycloakClient",
        "id",
        "KeycloakRealm",
        "name",
        "RESOURCE",
        rel_direction_right=False,
    ) == set(expected_rels)

    # Assert Clients are connected with Service Account
    expected_rels = {
        (
            "a8c34fe7-d67c-4917-b18a-a5058cf09714",
            "1859462c-4b8d-4e8f-9084-a5494a4f0437",
        ),
    }
    assert (
        check_rels(
            neo4j_session,
            "KeycloakClient",
            "id",
            "KeycloakUser",
            "id",
            "HAS_SERVICE_ACCOUNT",
            rel_direction_right=True,
        )
        == expected_rels
    )

    # Assert Clients are connected with Default Scopes
    expected_rels = []
    for client in tests.data.keycloak.clients.KEYCLOAK_CLIENTS:
        for scope in client.get("defaultClientScopes", []):
            expected_rels.append((client["id"], scope))
    assert len(expected_rels) > 0
    assert check_rels(
        neo4j_session,
        "KeycloakClient",
        "id",
        "KeycloakScope",
        "name",
        "HAS_DEFAULT_SCOPE",
        rel_direction_right=True,
    ) == set(expected_rels)

    # Assert Clients are connected with Optional Scopes
    expected_rels = []
    for client in tests.data.keycloak.clients.KEYCLOAK_CLIENTS:
        for scope in client.get("optionalClientScopes", []):
            expected_rels.append((client["id"], scope))
    assert len(expected_rels) > 0
    assert check_rels(
        neo4j_session,
        "KeycloakClient",
        "id",
        "KeycloakScope",
        "name",
        "HAS_OPTIONAL_SCOPE",
        rel_direction_right=True,
    ) == set(expected_rels)
