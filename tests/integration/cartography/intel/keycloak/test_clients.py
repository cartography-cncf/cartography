from copy import deepcopy
from unittest.mock import patch

import requests

import cartography.intel.keycloak.clients
import tests.data.keycloak.authenticationflows
import tests.data.keycloak.clients
import tests.data.keycloak.realms
from tests.integration.cartography.intel.keycloak.test_authenticationflows import (
    _ensure_local_neo4j_has_test_authenticationflows,
)
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
TEST_REALM_ID = tests.data.keycloak.realms.KEYCLOAK_REALMS[0].get("id")

# Default flows for the realm
FLOWS_BY_ALIAS = {
    f["alias"]: f["id"]
    for f in tests.data.keycloak.authenticationflows.KEYCLOAK_AUTHENTICATIONFLOWS
}
TEST_REALM_DEFAULT_FLOWS = {
    "browser": FLOWS_BY_ALIAS[
        tests.data.keycloak.realms.KEYCLOAK_REALMS[0].get("browserFlow")
    ],
    "registration": FLOWS_BY_ALIAS[
        tests.data.keycloak.realms.KEYCLOAK_REALMS[0].get("registrationFlow")
    ],
    "direct_grant": FLOWS_BY_ALIAS[
        tests.data.keycloak.realms.KEYCLOAK_REALMS[0].get("directGrantFlow")
    ],
    "reset_credentials": FLOWS_BY_ALIAS[
        tests.data.keycloak.realms.KEYCLOAK_REALMS[0].get("resetCredentialsFlow")
    ],
    "client_authentication": FLOWS_BY_ALIAS[
        tests.data.keycloak.realms.KEYCLOAK_REALMS[0].get("clientAuthenticationFlow")
    ],
    "docker_authentication": FLOWS_BY_ALIAS[
        tests.data.keycloak.realms.KEYCLOAK_REALMS[0].get("dockerAuthenticationFlow")
    ],
    "first_broker_login": FLOWS_BY_ALIAS[
        tests.data.keycloak.realms.KEYCLOAK_REALMS[0].get("firstBrokerLoginFlow")
    ],
}


def _ensure_local_neo4j_has_test_clients(neo4j_session):
    raw_data = deepcopy(tests.data.keycloak.clients.KEYCLOAK_CLIENTS)

    transformed_clients, service_accounts, flows_bindings = (
        cartography.intel.keycloak.clients.transform(
            raw_data,
            TEST_REALM_DEFAULT_FLOWS,
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
    cartography.intel.keycloak.clients.load_flow_bindings(
        neo4j_session,
        flows_bindings,
        TEST_REALM_ID,
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
        "REALM_ID": TEST_REALM_ID,
    }
    _ensure_local_neo4j_has_test_realms(neo4j_session)
    _ensure_local_neo4j_has_test_scopes(neo4j_session)
    _ensure_local_neo4j_has_test_authenticationflows(neo4j_session)

    # Act
    cartography.intel.keycloak.clients.sync(
        neo4j_session, api_session, "", common_job_parameters, TEST_REALM_DEFAULT_FLOWS
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

    # Assert Clients are connected with AuthenticationFlows
    expected_rels = set()
    for client in tests.data.keycloak.clients.KEYCLOAK_CLIENTS:
        for flow_name, flow_id in client.get(
            "authenticationFlowBindingOverrides", {}
        ).items():
            expected_rels.add((client["id"], flow_id))
    assert len(expected_rels) > 0
    actual_rels = check_rels(
        neo4j_session,
        "KeycloakClient",
        "id",
        "KeycloakAuthenticationFlow",
        "id",
        "USES",
        rel_direction_right=True,
    )
    assert len(actual_rels) > len(expected_rels)  # Ensure that default flows are loaded
    assert expected_rels.issubset(actual_rels)
