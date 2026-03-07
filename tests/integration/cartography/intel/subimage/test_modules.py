from unittest.mock import patch

import requests

import cartography.intel.subimage.modules
import tests.data.subimage.modules
from tests.integration.cartography.intel.subimage.test_team import (
    _ensure_local_neo4j_has_test_tenant,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_TENANT_ID = "tenant-abc-123"


@patch.object(
    cartography.intel.subimage.modules,
    "get",
    return_value=tests.data.subimage.modules.SUBIMAGE_MODULES_RAW,
)
def test_load_subimage_modules(mock_api, neo4j_session):
    # Arrange
    api_session = requests.Session()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "TENANT_ID": TEST_TENANT_ID,
        "BASE_URL": "https://app.example.com",
    }
    _ensure_local_neo4j_has_test_tenant(neo4j_session)

    # Act
    cartography.intel.subimage.modules.sync(
        neo4j_session,
        api_session,
        TEST_TENANT_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert nodes exist
    expected_nodes = {
        ("aws",),
        ("gcp",),
    }
    assert check_nodes(neo4j_session, "SubImageModule", ["id"]) == expected_nodes

    # Assert rels to tenant
    expected_rels = {
        ("aws", TEST_TENANT_ID),
        ("gcp", TEST_TENANT_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "SubImageModule",
            "id",
            "SubImageTenant",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_rels
    )


def test_transform():
    raw = {
        "aws": {"is_configured": True, "last_sync_status": "success"},
        "gcp": {"is_configured": False, "last_sync_status": None},
    }
    result = cartography.intel.subimage.modules.transform(raw)
    assert len(result) == 2
    assert {
        "module_name": "aws",
        "is_configured": True,
        "last_sync_status": "success",
    } in result
    assert {
        "module_name": "gcp",
        "is_configured": False,
        "last_sync_status": None,
    } in result
