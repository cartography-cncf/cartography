from unittest.mock import patch

import cartography.intel.googleworkspace.tenant
from cartography.intel.googleworkspace.tenant import sync_googleworkspace_tenant
from tests.data.googleworkspace.tenant import GOOGLEWORKSPACE_TENANT_DATA
from tests.integration.util import check_nodes

TEST_UPDATE_TAG = 123456789


def _ensure_local_neo4j_has_test_tenant(neo4j_session):
    cartography.intel.googleworkspace.tenant.load_googleworkspace_tenant(
        neo4j_session,
        GOOGLEWORKSPACE_TENANT_DATA,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.googleworkspace.tenant,
    "get_tenant",
    return_value=GOOGLEWORKSPACE_TENANT_DATA,
)
def test_sync_googleworkspace_tenant(_mock_get_tenant, neo4j_session):
    """
    Test that Google Workspace tenant sync correctly and creates proper nodes
    """
    # Arrange
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
    }

    # Act
    customer_id = sync_googleworkspace_tenant(
        neo4j_session,
        admin=None,  # Mocked
        googleworkspace_update_tag=TEST_UPDATE_TAG,
        common_job_parameters=common_job_parameters,
    )

    # Assert - Verify tenant was created
    expected_tenant_nodes = {
        ("ABC123CD", "simpson.corp"),
    }
    assert (
        check_nodes(neo4j_session, "GoogleWorkspaceTenant", ["id", "domain"])
        == expected_tenant_nodes
    )
    assert customer_id == "ABC123CD"
