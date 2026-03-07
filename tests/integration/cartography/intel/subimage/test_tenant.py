from unittest.mock import patch

import requests

import cartography.intel.subimage.tenant
import tests.data.subimage.tenant
from tests.integration.util import check_nodes

TEST_UPDATE_TAG = 123456789


@patch.object(
    cartography.intel.subimage.tenant,
    "get",
    return_value=tests.data.subimage.tenant.SUBIMAGE_TENANT,
)
def test_load_subimage_tenant(mock_api, neo4j_session):
    # Arrange
    api_session = requests.Session()

    # Act
    tenants = cartography.intel.subimage.tenant.get(
        api_session, "https://app.example.com"
    )
    cartography.intel.subimage.tenant.load_tenants(
        neo4j_session,
        tenants,
        TEST_UPDATE_TAG,
    )

    # Assert
    expected_nodes = {("tenant-abc-123", "acct-001")}
    assert (
        check_nodes(neo4j_session, "SubImageTenant", ["id", "account_id"])
        == expected_nodes
    )
