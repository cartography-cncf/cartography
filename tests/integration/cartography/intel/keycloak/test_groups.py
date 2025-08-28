from copy import deepcopy
from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.keycloak.groups
import tests.data.keycloak.groups
from tests.integration.cartography.intel.keycloak.test_realms import (
    _ensure_local_neo4j_has_test_realms,
)
from tests.integration.cartography.intel.keycloak.test_roles import (
    _ensure_local_neo4j_has_test_roles,
)
from tests.integration.cartography.intel.keycloak.test_users import (
    _ensure_local_neo4j_has_test_users,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_REALM = "simpson-corp"


@patch.object(
    cartography.intel.keycloak.groups,
    "get",
    return_value=deepcopy(tests.data.keycloak.groups.KEYCLOAK_GROUPS),
)
def test_load_keycloak_groups(mock_api, neo4j_session):
    # Arrange
    api_session = Mock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "REALM": TEST_REALM,
    }
    _ensure_local_neo4j_has_test_realms(neo4j_session)
    _ensure_local_neo4j_has_test_users(neo4j_session)
    _ensure_local_neo4j_has_test_roles(neo4j_session)

    # Act
    cartography.intel.keycloak.groups.sync(
        neo4j_session,
        api_session,
        "",
        common_job_parameters,
    )

    # Assert Groups exist
    expected_nodes = {
        (
            "0c371c4c-59e4-4520-8033-5aba5be98694",
            "Simpson Family",
        ),
        (
            "3279912a-4f73-43ee-afbf-3ed1d53a33ca",
            "Springfield Residents",
        ),
    }
    assert check_nodes(neo4j_session, "KeycloakGroup", ["id", "name"]) == expected_nodes

    # Assert Groups are connected with Realm
    expected_rels = {
        ("0c371c4c-59e4-4520-8033-5aba5be98694", TEST_REALM),
        ("3279912a-4f73-43ee-afbf-3ed1d53a33ca", TEST_REALM),
    }
    assert (
        check_rels(
            neo4j_session,
            "KeycloakGroup",
            "id",
            "KeycloakRealm",
            "name",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_rels
    )

    # Assert Groups are connected with Users
    expected_rels = {
        (
            "0c371c4c-59e4-4520-8033-5aba5be98694",
            "b34866c4-7c54-439d-82ab-f8c21bd2d81a",
        ),
        (
            "0c371c4c-59e4-4520-8033-5aba5be98694",
            "ccd37f3c-57de-423a-879e-f376de2839ec",
        ),
    }

    assert (
        check_rels(
            neo4j_session,
            "KeycloakGroup",
            "id",
            "KeycloakUser",
            "id",
            "MEMBER_OF",
            rel_direction_right=False,
        )
        == expected_rels
    )

    # Assert Groups are connected with other Groups
    expected_rels = {
        (
            "3279912a-4f73-43ee-afbf-3ed1d53a33ca",
            "0c371c4c-59e4-4520-8033-5aba5be98694",
        ),
    }

    assert (
        check_rels(
            neo4j_session,
            "KeycloakGroup",
            "id",
            "KeycloakGroup",
            "id",
            "SUBGROUP_OF",
            rel_direction_right=False,
        )
        == expected_rels
    )

    # Assert Groups are connected with Roles
    expected_rels = {
        (
            "0c371c4c-59e4-4520-8033-5aba5be98694",
            "b31f09b1-18f1-42b0-bbd4-4da5134da573",
        ),
        (
            "3279912a-4f73-43ee-afbf-3ed1d53a33ca",
            "174ab56d-57be-413e-a8f7-d370091be3df",
        ),
    }

    assert (
        check_rels(
            neo4j_session,
            "KeycloakGroup",
            "id",
            "KeycloakRole",
            "id",
            "GRANTS",
            rel_direction_right=True,
        )
        == expected_rels
    )
