from unittest.mock import patch

import cartography.intel.gcp.crm
import tests.data.gcp.crm
from tests.integration.util import check_nodes

TEST_UPDATE_TAG = 123456789
COMMON_JOB_PARAMS = {"UPDATE_TAG": TEST_UPDATE_TAG}


@patch.object(
    cartography.intel.gcp.crm.orgs,
    "get_gcp_organizations",
    return_value=tests.data.gcp.crm.GCP_ORGANIZATIONS,
)
def test_sync_gcp_organizations(_mock_get_orgs, neo4j_session):
    neo4j_session.run("MATCH (n) DETACH DELETE n")

    cartography.intel.gcp.crm.orgs.sync_gcp_organizations(
        neo4j_session, TEST_UPDATE_TAG, COMMON_JOB_PARAMS
    )

    assert check_nodes(neo4j_session, "GCPOrganization", ["id", "displayname"]) == {
        ("organizations/1337", "example.com"),
    }
