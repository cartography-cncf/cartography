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
    expected_nodes = [
        (s["id"], s["name"]) for s in tests.data.keycloak.scopes.KEYCLOAK_SCOPES
    ]
    assert len(expected_nodes) > 0
    assert check_nodes(neo4j_session, "KeycloakScope", ["id", "name"]) == set(
        expected_nodes
    )

    # Assert Scopes are connected with Realm
    expected_rels = [
        (s["id"], TEST_REALM) for s in tests.data.keycloak.scopes.KEYCLOAK_SCOPES
    ]
    assert len(expected_rels) > 0
    assert check_rels(
        neo4j_session,
        "KeycloakScope",
        "id",
        "KeycloakRealm",
        "name",
        "RESOURCE",
        rel_direction_right=False,
    ) == set(expected_rels)
