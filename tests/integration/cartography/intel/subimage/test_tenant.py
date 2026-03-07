import tests.data.subimage.tenant
from cartography.intel.subimage.tenant import load_tenants
from tests.integration.util import check_nodes

TEST_UPDATE_TAG = 123456789


def test_load_subimage_tenant(neo4j_session):
    # Act
    load_tenants(
        neo4j_session,
        tests.data.subimage.tenant.SUBIMAGE_TENANT,
        TEST_UPDATE_TAG,
    )

    # Assert
    expected_nodes = {("tenant-abc-123", "acct-001")}
    assert (
        check_nodes(neo4j_session, "SubImageTenant", ["id", "account_id"])
        == expected_nodes
    )
