from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.gcp.router
from tests.data.gcp.router import ROUTER_AGGREGATED_RESPONSE
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_PROJECT_ID = "project-abc"
TEST_VPC_ID = f"projects/{TEST_PROJECT_ID}/global/networks/default"


def _create_prerequisite_nodes(neo4j_session):
    neo4j_session.run(
        "MERGE (p:GCPProject {id: $project_id}) SET p.lastupdated = $tag",
        project_id=TEST_PROJECT_ID,
        tag=TEST_UPDATE_TAG,
    )
    neo4j_session.run(
        "MERGE (v:GCPVpc {id: $vpc_id}) SET v.lastupdated = $tag",
        vpc_id=TEST_VPC_ID,
        tag=TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.gcp.router,
    "get_gcp_routers",
    return_value=ROUTER_AGGREGATED_RESPONSE,
)
def test_sync_gcp_routers(mock_get_routers, neo4j_session):
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    _create_prerequisite_nodes(neo4j_session)
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "PROJECT_ID": TEST_PROJECT_ID,
    }

    cartography.intel.gcp.router.sync_gcp_routers(
        neo4j_session,
        MagicMock(),
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    assert check_nodes(
        neo4j_session,
        "GCPRouter",
        ["id", "name", "region", "network"],
    ) == {
        (
            f"projects/{TEST_PROJECT_ID}/regions/us-central1/routers/router-no-nats",
            "router-no-nats",
            "us-central1",
            TEST_VPC_ID,
        ),
        (
            f"projects/{TEST_PROJECT_ID}/regions/us-central1/routers/router-with-nats",
            "router-with-nats",
            "us-central1",
            TEST_VPC_ID,
        ),
    }

    assert check_nodes(
        neo4j_session,
        "GCPCloudNat",
        ["id", "name", "log_enabled", "log_filter"],
    ) == {
        (
            f"projects/{TEST_PROJECT_ID}/regions/us-central1/routers/"
            "router-with-nats/nats/nat-logging-on",
            "nat-logging-on",
            True,
            "ALL",
        ),
        (
            f"projects/{TEST_PROJECT_ID}/regions/us-central1/routers/"
            "router-with-nats/nats/nat-logging-off",
            "nat-logging-off",
            False,
            "ERRORS_ONLY",
        ),
        (
            f"projects/{TEST_PROJECT_ID}/regions/us-central1/routers/"
            "router-with-nats/nats/nat-no-log-config",
            "nat-no-log-config",
            None,
            None,
        ),
    }

    assert check_rels(
        neo4j_session,
        "GCPProject",
        "id",
        "GCPRouter",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (
            TEST_PROJECT_ID,
            f"projects/{TEST_PROJECT_ID}/regions/us-central1/routers/router-no-nats",
        ),
        (
            TEST_PROJECT_ID,
            f"projects/{TEST_PROJECT_ID}/regions/us-central1/routers/router-with-nats",
        ),
    }

    assert check_rels(
        neo4j_session,
        "GCPRouter",
        "id",
        "GCPVpc",
        "id",
        "ASSOCIATED_WITH",
        rel_direction_right=True,
    ) == {
        (
            f"projects/{TEST_PROJECT_ID}/regions/us-central1/routers/router-no-nats",
            TEST_VPC_ID,
        ),
        (
            f"projects/{TEST_PROJECT_ID}/regions/us-central1/routers/router-with-nats",
            TEST_VPC_ID,
        ),
    }

    assert check_rels(
        neo4j_session,
        "GCPRouter",
        "id",
        "GCPCloudNat",
        "id",
        "HAS_NAT",
        rel_direction_right=True,
    ) == {
        (
            f"projects/{TEST_PROJECT_ID}/regions/us-central1/routers/router-with-nats",
            f"projects/{TEST_PROJECT_ID}/regions/us-central1/routers/"
            "router-with-nats/nats/nat-logging-on",
        ),
        (
            f"projects/{TEST_PROJECT_ID}/regions/us-central1/routers/router-with-nats",
            f"projects/{TEST_PROJECT_ID}/regions/us-central1/routers/"
            "router-with-nats/nats/nat-logging-off",
        ),
        (
            f"projects/{TEST_PROJECT_ID}/regions/us-central1/routers/router-with-nats",
            f"projects/{TEST_PROJECT_ID}/regions/us-central1/routers/"
            "router-with-nats/nats/nat-no-log-config",
        ),
    }
