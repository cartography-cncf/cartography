from unittest.mock import patch

import requests

import cartography.intel.subimage.neo4jusers
import tests.data.subimage.neo4jusers
from tests.integration.cartography.intel.subimage.test_team import (
    _ensure_local_neo4j_has_test_tenant,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_TENANT_ID = "tenant-abc-123"


@patch.object(
    cartography.intel.subimage.neo4jusers,
    "get",
    return_value=tests.data.subimage.neo4jusers.SUBIMAGE_NEO4J_USERS_RAW,
)
def test_load_subimage_neo4jusers(mock_api, neo4j_session):
    # Arrange
    api_session = requests.Session()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "TENANT_ID": TEST_TENANT_ID,
        "BASE_URL": "https://app.example.com",
    }
    _ensure_local_neo4j_has_test_tenant(neo4j_session)

    # Act
    cartography.intel.subimage.neo4jusers.sync(
        neo4j_session,
        api_session,
        TEST_TENANT_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert nodes exist
    expected_nodes = {
        ("neo4j_admin",),
        ("neo4j_reader",),
    }
    assert check_nodes(neo4j_session, "SubImageNeo4jUser", ["id"]) == expected_nodes

    # Assert rels to tenant
    expected_rels = {
        ("neo4j_admin", TEST_TENANT_ID),
        ("neo4j_reader", TEST_TENANT_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "SubImageNeo4jUser",
            "id",
            "SubImageTenant",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_rels
    )


def test_transform():
    raw = {"usernames": ["user_a", "user_b"]}
    result = cartography.intel.subimage.neo4jusers.transform(raw)
    assert result == [{"username": "user_a"}, {"username": "user_b"}]
