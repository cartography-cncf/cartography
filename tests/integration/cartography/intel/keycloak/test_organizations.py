from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.keycloak.organizations
import tests.data.keycloak.organizations
from tests.integration.cartography.intel.keycloak.test_identityproviders import (
    _ensure_local_neo4j_has_test_identity_providers,
)
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


@patch.object(
    cartography.intel.keycloak.organizations,
    "get",
    return_value=tests.data.keycloak.organizations.KEYCLOAK_ORGANIZATIONS,
)
def test_load_keycloak_organizations(_mock_api, neo4j_session):
    # Arrange
    api_session = Mock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "REALM": TEST_REALM,
    }
    _ensure_local_neo4j_has_test_realms(neo4j_session)
    _ensure_local_neo4j_has_test_users(neo4j_session)
    _ensure_local_neo4j_has_test_identity_providers(neo4j_session)

    # Act
    cartography.intel.keycloak.organizations.sync(
        neo4j_session,
        api_session,
        "",
        common_job_parameters,
    )

    # Assert Organizations exist
    expected_nodes = {
        ("6f326c1f-5c52-4293-9d33-b15eed19c220", "springfield-powerplant-ltd"),
    }
    assert (
        check_nodes(neo4j_session, "KeycloakOrganization", ["id", "name"])
        == expected_nodes
    )

    # Assert Organization Domains exist
    expected_nodes = {
        ("6f326c1f-5c52-4293-9d33-b15eed19c220-burns-lovers.com", "burns-lovers.com"),
    }
    assert (
        check_nodes(neo4j_session, "KeycloakOrganizationDomain", ["id", "name"])
        == expected_nodes
    )

    # Assert Organizations are connected with Realm
    expected_rels = {
        ("6f326c1f-5c52-4293-9d33-b15eed19c220", TEST_REALM),
    }
    assert (
        check_rels(
            neo4j_session,
            "KeycloakOrganization",
            "id",
            "KeycloakRealm",
            "name",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_rels
    )

    # Assert Organization Domains are connected with Realm
    expected_rels = {
        ("6f326c1f-5c52-4293-9d33-b15eed19c220-burns-lovers.com", TEST_REALM),
    }
    assert (
        check_rels(
            neo4j_session,
            "KeycloakOrganizationDomain",
            "id",
            "KeycloakRealm",
            "name",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_rels
    )

    # Assert Organization Domains are connected with Organizations
    expected_rels = {
        (
            "6f326c1f-5c52-4293-9d33-b15eed19c220-burns-lovers.com",
            "6f326c1f-5c52-4293-9d33-b15eed19c220",
        ),
    }
    assert (
        check_rels(
            neo4j_session,
            "KeycloakOrganizationDomain",
            "id",
            "KeycloakOrganization",
            "id",
            "BELONGS_TO",
            rel_direction_right=True,
        )
        == expected_rels
    )

    # Assert Organizations are connected to Users
    expected_rels = {
        (
            "6f326c1f-5c52-4293-9d33-b15eed19c220",
            "b34866c4-7c54-439d-82ab-f8c21bd2d81a",
        ),
    }
    assert (
        check_rels(
            neo4j_session,
            "KeycloakOrganization",
            "id",
            "KeycloakUser",
            "id",
            "UNMANAGED_MEMBER_OF",
            rel_direction_right=False,
        )
        == expected_rels
    )

    # Assert Organizations are connected to Identity Providers
    expected_rels = {
        (
            "6f326c1f-5c52-4293-9d33-b15eed19c220",
            "8e6bcacd-9592-4009-8fb2-aca89656ccc0",
        ),
    }
    assert (
        check_rels(
            neo4j_session,
            "KeycloakOrganization",
            "id",
            "KeycloakIdentityProvider",
            "id",
            "ENFORCES",
            rel_direction_right=True,
        )
        == expected_rels
    )
