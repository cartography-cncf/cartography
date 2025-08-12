from copy import deepcopy
from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.keycloak.identityproviders
import tests.data.keycloak.identityproviders
from tests.integration.cartography.intel.keycloak.test_realms import (
    _ensure_local_neo4j_has_test_realms,
)
from tests.integration.cartography.intel.keycloak.test_users import (
    _ensure_local_neo4j_has_test_users,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_REALM = "simpson-corp"


def _ensure_local_neo4j_has_test_identity_providers(neo4j_session):
    raw_data = deepcopy(tests.data.keycloak.identityproviders.KEYCLOAK_IDPS)
    idps = cartography.intel.keycloak.identityproviders.transform(raw_data)
    cartography.intel.keycloak.identityproviders.load_identityproviders(
        neo4j_session,
        idps,
        TEST_REALM,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.keycloak.identityproviders,
    "get",
    return_value=deepcopy(tests.data.keycloak.identityproviders.KEYCLOAK_IDPS),
)
def test_load_keycloak_identityproviders(mock_api, neo4j_session):
    # Arrange
    api_session = Mock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "REALM": TEST_REALM,
    }
    _ensure_local_neo4j_has_test_realms(neo4j_session)
    _ensure_local_neo4j_has_test_users(neo4j_session)

    # Act
    cartography.intel.keycloak.identityproviders.sync(
        neo4j_session,
        api_session,
        "",
        common_job_parameters,
    )

    # Assert IdentityProviders exist
    expected_nodes = {
        (
            "8e6bcacd-9592-4009-8fb2-aca89656ccc0",
            "linkedin-openid-connect",
            "LinkedIn",
        ),
    }

    assert (
        check_nodes(
            neo4j_session, "KeycloakIdentityProvider", ["id", "alias", "display_name"]
        )
        == expected_nodes
    )

    # Assert IdentityProviders are connected with Realm
    expected_rels = {
        ("8e6bcacd-9592-4009-8fb2-aca89656ccc0", TEST_REALM),
    }
    assert (
        check_rels(
            neo4j_session,
            "KeycloakIdentityProvider",
            "id",
            "KeycloakRealm",
            "name",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_rels
    )

    # Assert IdentityProviders are connected with Users
    expected_rels = {
        (
            "8e6bcacd-9592-4009-8fb2-aca89656ccc0",
            "b34866c4-7c54-439d-82ab-f8c21bd2d81a",
        ),
    }
    assert (
        check_rels(
            neo4j_session,
            "KeycloakIdentityProvider",
            "id",
            "KeycloakUser",
            "id",
            "HAS_IDENTITY",
            rel_direction_right=False,
        )
        == expected_rels
    )
