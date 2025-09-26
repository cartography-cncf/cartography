from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.keycloak.realms
import tests.data.keycloak.realms
from tests.integration.util import check_nodes

TEST_UPDATE_TAG = 123456789


def _ensure_local_neo4j_has_test_realms(neo4j_session):
    cartography.intel.keycloak.realms.load_realms(
        neo4j_session,
        tests.data.keycloak.realms.KEYCLOAK_REALMS,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.keycloak.realms,
    "get",
    return_value=tests.data.keycloak.realms.KEYCLOAK_REALMS,
)
def test_load_keycloak_realms(mock_api, neo4j_session):
    """
    Ensure that realms actually get loaded
    """

    # Arrange
    api_session = Mock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
    }

    # Act
    cartography.intel.keycloak.realms.sync(
        neo4j_session,
        api_session,
        "",
        common_job_parameters,
    )

    # Assert Realms exist
    expected_nodes = {
        ("a18ee71e-2991-4987-8a9b-2ee3a338455b", "simpson-corp"),
    }
    assert check_nodes(neo4j_session, "KeycloakRealm", ["id", "name"]) == expected_nodes
