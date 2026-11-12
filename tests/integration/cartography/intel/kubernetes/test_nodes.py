from types import SimpleNamespace
from uuid import uuid4

from kubernetes.client.exceptions import ApiException

import cartography.intel.kubernetes.nodes as nodes_module
import cartography.intel.kubernetes.pods as pods_module
from cartography.intel.kubernetes.nodes import sync_nodes
from cartography.intel.kubernetes.pods import sync_pods
from tests.data.kubernetes.clusters import KUBERNETES_CLUSTER_IDS
from tests.data.kubernetes.clusters import KUBERNETES_CLUSTER_NAMES
from tests.data.kubernetes.nodes import RAW_CSI_NODES
from tests.data.kubernetes.nodes import RAW_NODES
from tests.data.kubernetes.nodes import RAW_PODS
from tests.data.kubernetes.nodes import RAW_SCALEWAY_NODES
from tests.data.kubernetes.nodes import SCALEWAY_INSTANCE_ID
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
CLUSTER_ID = KUBERNETES_CLUSTER_IDS[0]
CLUSTER_NAME = KUBERNETES_CLUSTER_NAMES[0]


def test_sync_nodes_and_runs_on(neo4j_session, monkeypatch):
    # Arrange
    monkeypatch.setattr(nodes_module, "get_nodes", lambda client: RAW_NODES)
    monkeypatch.setattr(nodes_module, "get_csi_nodes", lambda client: [])
    monkeypatch.setattr(
        pods_module,
        "get_pods",
        lambda client: RAW_PODS
        + [
            SimpleNamespace(
                metadata=SimpleNamespace(
                    uid=uuid4().hex,
                    name="arm-node-test-pod",
                    namespace="default",
                    creation_timestamp=None,
                    deletion_timestamp=None,
                    labels={},
                ),
                spec=SimpleNamespace(
                    containers=[
                        SimpleNamespace(
                            name="arm-node-test-container",
                            image="arm-node-test:latest",
                            image_pull_policy="IfNotPresent",
                            resources=None,
                            env=None,
                            env_from=None,
                            volume_mounts=None,
                        ),
                    ],
                    volumes=[],
                    node_name="my-arm-node",
                    service_account_name="default",
                ),
                status=SimpleNamespace(phase="running", container_statuses=[]),
            ),
        ],
    )

    client = SimpleNamespace(name=CLUSTER_NAME, gke_cluster=None)
    common_job_parameters = {"UPDATE_TAG": TEST_UPDATE_TAG, "CLUSTER_ID": CLUSTER_ID}

    # Arrange: the backing EC2 instance must already exist for the IS_INSTANCE
    # link to be created when the node is loaded.
    neo4j_session.run(
        "MERGE (i:AWSEC2Instance {id: 'i-0123456789abcdef0'}) "
        "SET i.instanceid = 'i-0123456789abcdef0'"
    )

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
    assert check_nodes(
        neo4j_session,
        "KubernetesNode",
        ["name", "gpu_capacity", "gpu_allocatable", "gpu_product"],
    ) == {
        ("my-node", 8, 8, "NVIDIA-H200"),
        ("my-arm-node", None, None, None),
    }

    # Assert: pod is linked to its scheduled node
    assert check_rels(
        neo4j_session,
        "KubernetesPod",
        "name",
        "KubernetesNode",
        "name",
        "RUNS_ON",
    ) == {
        ("arm-node-test-pod", "my-arm-node"),
        ("node-test-pod", "my-node"),
    }

    # Assert: EKS node is linked to its backing EC2 instance; the non-AWS
    # node (provider_id None) produces no link.
    assert check_rels(
        neo4j_session,
        "KubernetesNode",
        "name",
        "AWSEC2Instance",
        "id",
        "IS_INSTANCE",
    ) == {
        ("my-node", "i-0123456789abcdef0"),
    }

    # Assert: pod and container inherit normalized runtime architecture
    assert check_nodes(
        neo4j_session,
        "KubernetesPod",
        ["name", "architecture_normalized"],
    ) == {
        ("arm-node-test-pod", "arm64"),
        ("node-test-pod", "amd64"),
    }
    assert check_nodes(
        neo4j_session,
        "KubernetesContainer",
        ["name", "architecture_normalized"],
    ) == {
        ("arm-node-test-container", "arm64"),
        ("node-test-container", "amd64"),
    }


def test_sync_nodes_links_scaleway_instance_from_csi_node(neo4j_session, monkeypatch):
    # Arrange: a self-managed node whose providerID does not reference
    # Scaleway; only its CSINode object carries the Instance server id.
    monkeypatch.setattr(
        nodes_module, "get_nodes", lambda client: RAW_NODES + RAW_SCALEWAY_NODES
    )
    monkeypatch.setattr(nodes_module, "get_csi_nodes", lambda client: RAW_CSI_NODES)
    client = SimpleNamespace(name=CLUSTER_NAME, gke_cluster=None)
    common_job_parameters = {"UPDATE_TAG": TEST_UPDATE_TAG, "CLUSTER_ID": CLUSTER_ID}
    neo4j_session.run(
        "MERGE (i:ScalewayInstance {id: $id})",
        id=SCALEWAY_INSTANCE_ID,
    )
    # The nodes attach to their cluster, which previously synced CSI node IDs
    # are read back through.
    neo4j_session.run("MERGE (c:KubernetesCluster {id: $id})", id=CLUSTER_ID)

    # Act
    sync_nodes(neo4j_session, client, TEST_UPDATE_TAG, common_job_parameters)

    # Assert: the CSI driver node IDs are recorded on the node
    assert check_nodes(
        neo4j_session,
        "KubernetesNode",
        ["name", "scaleway_instance_id", "csi_node_ids"],
    ) == {
        ("my-node", None, None),
        ("my-arm-node", None, None),
        (
            "my-scaleway-node",
            SCALEWAY_INSTANCE_ID,
            f'{{"csi.scaleway.com": "fr-par-2/{SCALEWAY_INSTANCE_ID}"}}',
        ),
    }

    # Assert: only the Scaleway node is linked to the Scaleway Instance
    assert check_rels(
        neo4j_session,
        "KubernetesNode",
        "name",
        "ScalewayInstance",
        "id",
        "IS_INSTANCE",
    ) == {
        ("my-scaleway-node", SCALEWAY_INSTANCE_ID),
    }

    # Act: a later sync is denied `list csinodes`
    def _forbidden(client):
        raise ApiException(status=403)

    monkeypatch.setattr(nodes_module, "get_csi_nodes", _forbidden)
    later_update_tag = TEST_UPDATE_TAG + 1
    sync_nodes(
        neo4j_session,
        client,
        later_update_tag,
        {"UPDATE_TAG": later_update_tag, "CLUSTER_ID": CLUSTER_ID},
    )

    # Assert: the previously synced CSI node IDs and the link they produce are
    # kept rather than cleared by a denied list
    assert check_nodes(
        neo4j_session,
        "KubernetesNode",
        ["name", "scaleway_instance_id", "lastupdated"],
    ) == {
        ("my-node", None, later_update_tag),
        ("my-arm-node", None, later_update_tag),
        ("my-scaleway-node", SCALEWAY_INSTANCE_ID, later_update_tag),
    }
    assert check_rels(
        neo4j_session,
        "KubernetesNode",
        "name",
        "ScalewayInstance",
        "id",
        "IS_INSTANCE",
    ) == {
        ("my-scaleway-node", SCALEWAY_INSTANCE_ID),
    }
