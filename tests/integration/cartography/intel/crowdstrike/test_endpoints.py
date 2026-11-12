import cartography.intel.crowdstrike.endpoints
import tests.data.crowdstrike.endpoints
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
HOST_ID = "00000000000000000000000000000000"


def test_load_host_data(neo4j_session, *args):
    neo4j_session.run(
        "MERGE (i:AWSEC2Instance {id: 'i-01'}) SET i.lastupdated = $tag",
        tag=TEST_UPDATE_TAG,
    )
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
    ) == {(HOST_ID, "alice@example.com")}
    assert check_rels(
        neo4j_session,
        "CrowdstrikeHost",
        "id",
        "AWSEC2Instance",
        "id",
        "IS_INSTANCE",
    ) == {(HOST_ID, "i-01")}


def test_load_host_data_does_not_link_fargate_tasks(neo4j_session, *args):
    neo4j_session.run("MATCH (n:CrowdstrikeHost) DETACH DELETE n")
    neo4j_session.run(
        "MERGE (i:AWSEC2Instance {id: 'i-01'}) SET i.lastupdated = $tag",
        tag=TEST_UPDATE_TAG,
    )
    data = [
        {**host, "service_provider": "AWS_ECS_FARGATE"}
        for host in tests.data.crowdstrike.endpoints.GET_HOSTS
    ]
    cartography.intel.crowdstrike.endpoints.load_host_data(
        neo4j_session,
        data,
        TEST_UPDATE_TAG,
    )

    assert check_nodes(neo4j_session, "CrowdstrikeHost", ["id"]) == {(HOST_ID,)}
    assert (
        check_rels(
            neo4j_session,
            "CrowdstrikeHost",
            "id",
            "AWSEC2Instance",
            "id",
            "IS_INSTANCE",
        )
        == set()
    )
