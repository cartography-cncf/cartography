import pytest

from cartography.intel.kubernetes.clusters import load_kubernetes_cluster
from cartography.intel.kubernetes.nodes import cleanup
from cartography.intel.kubernetes.nodes import load_nodes
from tests.data.kubernetes.clusters import KUBERNETES_CLUSTER_DATA
from tests.data.kubernetes.clusters import KUBERNETES_CLUSTER_IDS
from tests.data.kubernetes.clusters import KUBERNETES_CLUSTER_NAMES
from tests.data.kubernetes.nodes import KUBERNETES_CLUSTER_1_NODES_DATA
from tests.data.kubernetes.nodes import KUBERNETES_NODES_LIVE_REDACTED_DATA
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789


@pytest.fixture
def _create_test_cluster(neo4j_session):
    load_kubernetes_cluster(
        neo4j_session,
        KUBERNETES_CLUSTER_DATA,
        TEST_UPDATE_TAG,
    )
    yield
    neo4j_session.run("MATCH (n:KubernetesNode) DETACH DELETE n")
    neo4j_session.run("MATCH (n:KubernetesCluster) DETACH DELETE n")


def test_load_kubernetes_nodes(neo4j_session, _create_test_cluster):
    load_nodes(
        neo4j_session,
        KUBERNETES_CLUSTER_1_NODES_DATA,
        TEST_UPDATE_TAG,
        KUBERNETES_CLUSTER_IDS[0],
        KUBERNETES_CLUSTER_NAMES[0],
    )

    assert check_nodes(
        neo4j_session,
        "KubernetesNode",
        ["name", "architecture", "ready"],
    ) == {
        ("my-node", "arm64", True),
    }

    assert check_rels(
        neo4j_session,
        "KubernetesCluster",
        "id",
        "KubernetesNode",
        "name",
        "RESOURCE",
    ) == {
        (KUBERNETES_CLUSTER_IDS[0], "my-node"),
    }


def test_load_kubernetes_nodes_live_redacted(neo4j_session, _create_test_cluster):
    load_nodes(
        neo4j_session,
        KUBERNETES_NODES_LIVE_REDACTED_DATA,
        TEST_UPDATE_TAG,
        KUBERNETES_CLUSTER_IDS[0],
        KUBERNETES_CLUSTER_NAMES[0],
    )

    assert check_nodes(
        neo4j_session,
        "KubernetesNode",
        ["name", "architecture", "container_runtime_version"],
    ) == {
        ("ip-172-31-76-117.ec2.internal", "amd64", "containerd://1.7.27"),
    }


def test_kubernetes_nodes_cleanup(neo4j_session, _create_test_cluster):
    load_nodes(
        neo4j_session,
        KUBERNETES_CLUSTER_1_NODES_DATA,
        TEST_UPDATE_TAG,
        KUBERNETES_CLUSTER_IDS[0],
        KUBERNETES_CLUSTER_NAMES[0],
    )
    cleanup(
        neo4j_session,
        {"UPDATE_TAG": TEST_UPDATE_TAG + 1, "CLUSTER_ID": KUBERNETES_CLUSTER_IDS[0]},
    )

    assert check_nodes(neo4j_session, "KubernetesNode", ["name"]) == set()
