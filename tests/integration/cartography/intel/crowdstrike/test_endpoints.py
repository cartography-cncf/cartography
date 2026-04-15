import cartography.intel.crowdstrike.endpoints
import tests.data.crowdstrike.endpoints
from tests.integration.util import check_nodes

TEST_UPDATE_TAG = 123456789


def test_load_host_data(neo4j_session, *args):
    data = tests.data.crowdstrike.endpoints.GET_HOSTS
    cartography.intel.crowdstrike.endpoints.load_host_data(
        neo4j_session,
        data,
        TEST_UPDATE_TAG,
    )

    assert check_nodes(
        neo4j_session,
        "CrowdstrikeHost",
        ["id", "email"],
    ) == {("00000000000000000000000000000000", "alice@example.com")}
