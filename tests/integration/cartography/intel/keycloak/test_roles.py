from unittest.mock import patch

import requests

import cartography.intel.keycloak.roles
import tests.data.keycloak.clients
import tests.data.keycloak.roles
import tests.data.keycloak.scopes
from tests.integration.cartography.intel.keycloak.test_clients import (
    _ensure_local_neo4j_has_test_clients,
)
from tests.integration.cartography.intel.keycloak.test_realms import (
    _ensure_local_neo4j_has_test_realms,
)
from tests.integration.cartography.intel.keycloak.test_scopes import (
    _ensure_local_neo4j_has_test_scopes,
)
from tests.integration.cartography.intel.keycloak.test_users import (
    _ensure_local_neo4j_has_test_users,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_REALM = "simpson-corp"


def _ensure_local_neo4j_has_test_roles(neo4j_session):
    transformed_roles = cartography.intel.keycloak.roles.transform(
        tests.data.keycloak.roles.KEYCLOAK_ROLES,
        tests.data.keycloak.roles.KEYCLOAK_ROLES_MAPPING,
    )
    cartography.intel.keycloak.roles.load_roles(
        neo4j_session,
        transformed_roles,
        TEST_REALM,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.keycloak.roles,
    "get",
    return_value=tests.data.keycloak.roles.KEYCLOAK_ROLES,
)
@patch.object(
    cartography.intel.keycloak.roles,
    "get_mapping",
    return_value=tests.data.keycloak.roles.KEYCLOAK_ROLES_MAPPING,
)
def test_load_keycloak_roles(_, __, neo4j_session):
    # Arrange
    api_session = requests.Session()
    common_job_parameters = {"UPDATE_TAG": TEST_UPDATE_TAG, "REALM": TEST_REALM}
    _ensure_local_neo4j_has_test_realms(neo4j_session)
    _ensure_local_neo4j_has_test_users(neo4j_session)
    _ensure_local_neo4j_has_test_clients(neo4j_session)
    _ensure_local_neo4j_has_test_scopes(neo4j_session)
    client_ids = [c["id"] for c in tests.data.keycloak.clients.KEYCLOAK_CLIENTS]
    scope_ids = [s["id"] for s in tests.data.keycloak.scopes.KEYCLOAK_SCOPES]

    # Act
    cartography.intel.keycloak.roles.sync(
        neo4j_session, api_session, "", common_job_parameters, client_ids, scope_ids
    )

    # Assert Roles exist
    expected_nodes = [
        (r["id"], r["name"]) for r in tests.data.keycloak.roles.KEYCLOAK_ROLES
    ]
    assert len(expected_nodes) > 0
    assert check_nodes(neo4j_session, "KeycloakRole", ["id", "name"]) == set(
        expected_nodes
    )

    # Assert Roles are connected with Realm
    expected_rels = [
        (r["id"], TEST_REALM) for r in tests.data.keycloak.roles.KEYCLOAK_ROLES
    ]
    assert len(expected_rels) > 0
    assert check_rels(
        neo4j_session,
        "KeycloakRole",
        "id",
        "KeycloakRealm",
        "name",
        "RESOURCE",
        rel_direction_right=False,
    ) == set(expected_rels)

    # Assert Roles are connected with Client
    expected_rels = []
    for role in tests.data.keycloak.roles.KEYCLOAK_ROLES:
        if not role.get("clientRole", False):
            continue
        expected_rels.append((role["id"], role["containerId"]))
    assert len(expected_rels) > 0
    assert check_rels(
        neo4j_session,
        "KeycloakRole",
        "id",
        "KeycloakClient",
        "id",
        "DEFINES",
        rel_direction_right=False,
    ) == set(expected_rels)

    # Check composite roles are correctly loaded
    expected_rels = []
    for role in tests.data.keycloak.roles.KEYCLOAK_ROLES:
        for cr in role.get("_composite_roles", []):
            expected_rels.append((role["id"], cr))
    assert len(expected_rels) > 0
    assert check_rels(
        neo4j_session,
        "KeycloakRole",
        "id",
        "KeycloakRole",
        "id",
        "INCLUDES",
        rel_direction_right=True,
    ) == set(expected_rels)

    # Check roles direct member
    expected_rels = []
    for role in tests.data.keycloak.roles.KEYCLOAK_ROLES:
        for member in role.get("_direct_members", []):
            expected_rels.append((role["id"], member))
    assert len(expected_rels) > 0
    assert check_rels(
        neo4j_session,
        "KeycloakRole",
        "id",
        "KeycloakUser",
        "id",
        "ASSUME_ROLE",
        rel_direction_right=False,
    ) == set(expected_rels)

    # Check roles / scopes mapping
    expected_rels = []
    for role_id, mappings in tests.data.keycloak.roles.KEYCLOAK_ROLES_MAPPING.items():
        for mapping in mappings.get("clientMappings", {}).values():
            for element in mapping.get("mappings", []):
                expected_rels.append((role_id, element["id"]))
        for mapping in mappings.get("realmMappings", {}):
            expected_rels.append((role_id, mapping["id"]))
    assert len(expected_rels) > 0
    assert check_rels(
        neo4j_session,
        "KeycloakScope",
        "id",
        "KeycloakRole",
        "id",
        "GRANTS",
        rel_direction_right=False,
    ) == set(expected_rels)
