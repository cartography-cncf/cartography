import cartography.intel.gcp.crm
import tests.data.gcp.crm
from tests.integration.util import check_nodes

TEST_UPDATE_TAG = 123456789
COMMON_JOB_PARAMS = {"UPDATE_TAG": TEST_UPDATE_TAG}


def test_load_gcp_organizations(neo4j_session):
    neo4j_session.run("MATCH (n) DETACH DELETE n")

    cartography.intel.gcp.crm.orgs.load_gcp_organizations(
        neo4j_session,
        tests.data.gcp.crm.GCP_ORGANIZATIONS,
        TEST_UPDATE_TAG,
    )

    assert check_nodes(neo4j_session, "GCPOrganization", ["id", "displayname"]) == {
        ("organizations/1337", "example.com"),
    }
