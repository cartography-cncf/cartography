from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.keycloak.authenticationflows
import tests.data.keycloak.authenticationflows
from tests.integration.cartography.intel.keycloak.test_realms import (
    _ensure_local_neo4j_has_test_realms,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_REALM = "simpson-corp"


def _ensure_local_neo4j_has_test_authenticationflows(neo4j_session):
    cartography.intel.keycloak.authenticationflows.load_authenticationflows(
        neo4j_session,
        tests.data.keycloak.authenticationflows.KEYCLOAK_AUTHENTICATIONFLOWS,
        TEST_REALM,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.keycloak.authenticationflows,
    "get",
    return_value=tests.data.keycloak.authenticationflows.KEYCLOAK_AUTHENTICATIONFLOWS,
)
def test_load_keycloak_authenticationflows(_mock_api, neo4j_session):
    """
    Ensure that authentication flows actually get loaded
    """

    # Arrange
    api_session = Mock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "REALM": TEST_REALM,
    }
    _ensure_local_neo4j_has_test_realms(neo4j_session)

    # Act
    cartography.intel.keycloak.authenticationflows.sync(
        neo4j_session,
        api_session,
        "",
        common_job_parameters,
    )

    # Assert Authentication Flows exist
    expected_nodes = [
        (f["id"], f["alias"])
        for f in tests.data.keycloak.authenticationflows.KEYCLOAK_AUTHENTICATIONFLOWS
    ]
    assert len(expected_nodes) > 0
    assert check_nodes(
        neo4j_session, "KeycloakAuthenticationFlow", ["id", "alias"]
    ) == set(expected_nodes)

    # Assert Authentication Flows are connected with Realm
    expected_rels = [
        (flow["id"], TEST_REALM)
        for flow in tests.data.keycloak.authenticationflows.KEYCLOAK_AUTHENTICATIONFLOWS
    ]
    assert check_rels(
        neo4j_session,
        "KeycloakAuthenticationFlow",
        "id",
        "KeycloakRealm",
        "name",
        "RESOURCE",
        rel_direction_right=False,
    ) == set(expected_rels)
