from unittest.mock import patch

import requests

import cartography.intel.nullify.users
import tests.data.nullify.users
from tests.integration.cartography.intel.nullify.test_repositories import (
    _ensure_local_neo4j_has_test_tenant,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_TENANT = "acme"


def _ensure_local_neo4j_has_test_users(neo4j_session):
    _ensure_local_neo4j_has_test_tenant(neo4j_session)
    cartography.intel.nullify.users.load_users(
        neo4j_session,
        tests.data.nullify.users.NULLIFY_USERS,
        TEST_TENANT,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.nullify.users,
    "get",
    return_value=tests.data.nullify.users.NULLIFY_USERS,
)
def test_load_nullify_users(mock_api, neo4j_session):
    # Arrange
    api_session = requests.Session()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "TENANT_ID": TEST_TENANT,
        "BASE_URL": "https://api.acme.nullify.ai",
    }
    _ensure_local_neo4j_has_test_tenant(neo4j_session)

    # Act
    cartography.intel.nullify.users.sync(
        neo4j_session,
        api_session,
        "https://api.acme.nullify.ai",
        TEST_TENANT,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert users exist
    assert check_nodes(neo4j_session, "NullifyUser", ["id", "email"]) == {
        ("U1", "marge@acme.io"),
        ("U2", "homer@acme.io"),
    }

    # Assert users are scoped to the tenant
    assert check_rels(
        neo4j_session,
        "NullifyUser",
        "id",
        "NullifyTenant",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        ("U1", TEST_TENANT),
        ("U2", TEST_TENANT),
    }
