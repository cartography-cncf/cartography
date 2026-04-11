from types import SimpleNamespace

import cartography.intel.kubernetes.nodes as nodes_module
import cartography.intel.kubernetes.pods as pods_module
from cartography.intel.kubernetes.nodes import sync_nodes
from cartography.intel.kubernetes.pods import sync_pods
from tests.data.kubernetes.clusters import KUBERNETES_CLUSTER_IDS
from tests.data.kubernetes.clusters import KUBERNETES_CLUSTER_NAMES
from tests.data.kubernetes.nodes import RAW_NODES
from tests.data.kubernetes.nodes import RAW_PODS
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
CLUSTER_ID = KUBERNETES_CLUSTER_IDS[0]
CLUSTER_NAME = KUBERNETES_CLUSTER_NAMES[0]


def test_sync_nodes_and_runs_on(neo4j_session, monkeypatch):
    # Arrange
    monkeypatch.setattr(nodes_module, "get_nodes", lambda client: RAW_NODES)
    monkeypatch.setattr(pods_module, "get_pods", lambda client: RAW_PODS)

    client = SimpleNamespace(name=CLUSTER_NAME)
    common_job_parameters = {"UPDATE_TAG": TEST_UPDATE_TAG, "CLUSTER_ID": CLUSTER_ID}

    # Act
    node_arch_map = sync_nodes(
        neo4j_session, client, TEST_UPDATE_TAG, common_job_parameters
    )
    sync_pods(
        neo4j_session,
        client,
        TEST_UPDATE_TAG,
        common_job_parameters,
        node_arch_map=node_arch_map,
    )

    # Assert: nodes are in the graph
    assert check_nodes(neo4j_session, "KubernetesNode", ["name"]) == {
        ("my-node",),
        ("my-arm-node",),
    }

    # Assert: pod is linked to its scheduled node
    assert check_rels(
        neo4j_session,
        "KubernetesPod",
        "name",
        "KubernetesNode",
        "name",
        "RUNS_ON",
    ) == {("node-test-pod", "my-node")}

    # Assert: pod and container inherit normalized runtime architecture
    assert check_nodes(
        neo4j_session,
        "KubernetesPod",
        ["name", "architecture_normalized"],
    ) == {("node-test-pod", "amd64")}
    assert check_nodes(
        neo4j_session,
        "KubernetesContainer",
        ["name", "architecture_normalized"],
    ) == {("node-test-container", "amd64")}
