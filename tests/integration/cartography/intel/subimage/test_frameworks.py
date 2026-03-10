from unittest.mock import patch

import requests

import cartography.intel.subimage.frameworks
import tests.data.subimage.frameworks
from tests.integration.cartography.intel.subimage.test_team import (
    _ensure_local_neo4j_has_test_tenant,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_TENANT_ID = "tenant-abc-123"


@patch.object(
    cartography.intel.subimage.frameworks,
    "get",
    return_value=tests.data.subimage.frameworks.SUBIMAGE_FRAMEWORKS,
)
def test_load_subimage_frameworks(mock_api, neo4j_session):
    # Arrange
    api_session = requests.Session()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "TENANT_ID": TEST_TENANT_ID,
        "BASE_URL": "https://app.example.com",
    }
    _ensure_local_neo4j_has_test_tenant(neo4j_session)

    # Act
    cartography.intel.subimage.frameworks.sync(
        neo4j_session,
        api_session,
        TEST_TENANT_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert nodes exist
    expected_nodes = {
        ("fw-cis-aws-1.5", "CIS AWS"),
        ("fw-nist-800-53", "NIST"),
    }
    assert (
        check_nodes(neo4j_session, "SubImageFramework", ["id", "short_name"])
        == expected_nodes
    )

    # Assert rels to tenant
    expected_rels = {
        ("fw-cis-aws-1.5", TEST_TENANT_ID),
        ("fw-nist-800-53", TEST_TENANT_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "SubImageFramework",
            "id",
            "SubImageTenant",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_rels
    )
