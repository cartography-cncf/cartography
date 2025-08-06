from unittest.mock import patch

import requests

import cartography.intel.keycloak.scopes
import tests.data.keycloak.scopes
from tests.integration.cartography.intel.keycloak.test_realms import (
    _ensure_local_neo4j_has_test_realms,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_REALM = "simpson-corp"


def _ensure_local_neo4j_has_test_scopes(neo4j_session):
    cartography.intel.keycloak.scopes.load_scopes(
        neo4j_session,
        tests.data.keycloak.scopes.KEYCLOAK_SCOPES,
        TEST_REALM,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.keycloak.scopes,
    "get",
    return_value=tests.data.keycloak.scopes.KEYCLOAK_SCOPES,
)
def test_load_keycloak_scopes(mock_api, neo4j_session):
    # Arrange
    api_session = requests.Session()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "REALM": TEST_REALM,
    }
    _ensure_local_neo4j_has_test_realms(neo4j_session)

    # Act
    cartography.intel.keycloak.scopes.sync(
        neo4j_session,
        api_session,
        "",
        common_job_parameters,
    )

    # Assert Scopes exist
    expected_nodes = {
        (
            "0908dc73-29f1-4374-851e-fce191204d72",
            "acr",
        ),
        (
            "17f2be1d-e95a-4f55-b56e-c60576f5cbf6",
            "shutdown_control",
        ),
        (
            "1dc4ab12-3048-43eb-88f0-8cd46aa39b05",
            "role_list",
        ),
        (
            "2d557704-531d-479b-9720-c548985742a0",
            "phone",
        ),
        (
            "2e97d81f-2df1-47e0-8d6d-c0adfd3948f4",
            "email",
        ),
        (
            "3729a739-d111-435f-8425-24596d4beae5",
            "address",
        ),
        (
            "7f477610-425d-4836-b615-1a3b37d00773",
            "roles",
        ),
        (
            "b3e8d836-8a10-4e42-bb8d-991bf18e7130",
            "profile",
        ),
        (
            "b49bbd00-3ea0-4177-bf5e-eb33a1b11b51",
            "web-origins",
        ),
        (
            "b6853ac9-a428-4cdc-a61e-0147c8f37fc5",
            "offline_access",
        ),
        (
            "c066c2ec-b4f9-4416-a8ca-e0f11df3c84c",
            "organization",
        ),
        (
            "c51245de-fac8-4b86-89f4-452466ae4987",
            "saml_organization",
        ),
        (
            "cedca2b9-9637-4477-8546-e7e65547c0f4",
            "service_account",
        ),
        (
            "e273eb7c-6ed1-427a-b292-d70d0fe6d6a1",
            "commission_voter",
        ),
        (
            "e824414b-facb-4277-90c1-a187b589ed7b",
            "microprofile-jwt",
        ),
        (
            "f312d0c8-a00c-4651-b1de-11c568df7422",
            "basic",
        ),
    }
    assert check_nodes(neo4j_session, "KeycloakScope", ["id", "name"]) == expected_nodes

    # Assert Scopes are connected with Realm
    expected_rels = {
        ("e824414b-facb-4277-90c1-a187b589ed7b", TEST_REALM),
        ("1dc4ab12-3048-43eb-88f0-8cd46aa39b05", TEST_REALM),
        ("f312d0c8-a00c-4651-b1de-11c568df7422", TEST_REALM),
        ("17f2be1d-e95a-4f55-b56e-c60576f5cbf6", TEST_REALM),
        ("c51245de-fac8-4b86-89f4-452466ae4987", TEST_REALM),
        ("2d557704-531d-479b-9720-c548985742a0", TEST_REALM),
        ("b3e8d836-8a10-4e42-bb8d-991bf18e7130", TEST_REALM),
        ("7f477610-425d-4836-b615-1a3b37d00773", TEST_REALM),
        ("b6853ac9-a428-4cdc-a61e-0147c8f37fc5", TEST_REALM),
        ("cedca2b9-9637-4477-8546-e7e65547c0f4", TEST_REALM),
        ("c066c2ec-b4f9-4416-a8ca-e0f11df3c84c", TEST_REALM),
        ("0908dc73-29f1-4374-851e-fce191204d72", TEST_REALM),
        ("3729a739-d111-435f-8425-24596d4beae5", TEST_REALM),
        ("e273eb7c-6ed1-427a-b292-d70d0fe6d6a1", TEST_REALM),
        ("b49bbd00-3ea0-4177-bf5e-eb33a1b11b51", TEST_REALM),
        ("2e97d81f-2df1-47e0-8d6d-c0adfd3948f4", TEST_REALM),
    }
    assert (
        check_rels(
            neo4j_session,
            "KeycloakScope",
            "id",
            "KeycloakRealm",
            "name",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_rels
    )


# WIP: Test scopes / roles mapping
