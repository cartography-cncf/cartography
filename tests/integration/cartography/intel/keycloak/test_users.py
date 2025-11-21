from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.keycloak.users
import tests.data.keycloak.users
from tests.integration.cartography.intel.keycloak.test_realms import (
    _ensure_local_neo4j_has_test_realms,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_REALM = "simpson-corp"


def _ensure_local_neo4j_has_test_users(neo4j_session):
    cartography.intel.keycloak.users.load_users(
        neo4j_session,
        tests.data.keycloak.users.KEYCLOAK_USERS,
        TEST_REALM,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.keycloak.users,
    "get",
    return_value=tests.data.keycloak.users.KEYCLOAK_USERS,
)
def test_load_keycloak_users(mock_api, neo4j_session):
    # Arrange
    api_session = Mock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "REALM": TEST_REALM,
    }
    _ensure_local_neo4j_has_test_realms(neo4j_session)

    # Act
    cartography.intel.keycloak.users.sync(
        neo4j_session,
        api_session,
        "",
        common_job_parameters,
    )

    # Assert Users exist
    expected_nodes = {
        ("b34866c4-7c54-439d-82ab-f8c21bd2d81a", "hjsimpson@simpson.corp"),
        ("ccd37f3c-57de-423a-879e-f376de2839ec", "mbsimpson@simpson.corp"),
    }
    assert check_nodes(neo4j_session, "KeycloakUser", ["id", "email"]) == expected_nodes

    # Assert Users are connected with Realm
    expected_rels = {
        ("b34866c4-7c54-439d-82ab-f8c21bd2d81a", "simpson-corp"),
        ("ccd37f3c-57de-423a-879e-f376de2839ec", "simpson-corp"),
    }
    assert (
        check_rels(
            neo4j_session,
            "KeycloakUser",
            "id",
            "KeycloakRealm",
            "name",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_rels
    )
