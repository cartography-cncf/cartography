import pytest

from cartography.intel.kubernetes.clusters import load_kubernetes_cluster
from cartography.intel.kubernetes.namespaces import load_namespaces
from cartography.intel.kubernetes.pods import cleanup
from cartography.intel.kubernetes.pods import load_containers
from cartography.intel.kubernetes.pods import load_pods
from tests.data.kubernetes.clusters import KUBERNETES_CLUSTER_DATA
from tests.data.kubernetes.clusters import KUBERNETES_CLUSTER_IDS
from tests.data.kubernetes.clusters import KUBERNETES_CLUSTER_NAMES
from tests.data.kubernetes.namespaces import KUBERNETES_CLUSTER_1_NAMESPACES_DATA
from tests.data.kubernetes.namespaces import KUBERNETES_CLUSTER_2_NAMESPACES_DATA
from tests.data.kubernetes.pods import KUBERNETES_CONTAINER_DATA
from tests.data.kubernetes.pods import KUBERNETES_PODS_DATA
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789


@pytest.fixture
def _create_test_cluster(neo4j_session):
    # Setup multiple clusters and namespaces
    load_kubernetes_cluster(
        neo4j_session,
        KUBERNETES_CLUSTER_DATA,
        TEST_UPDATE_TAG,
    )
    load_namespaces(
        neo4j_session,
        KUBERNETES_CLUSTER_1_NAMESPACES_DATA,
        TEST_UPDATE_TAG,
        KUBERNETES_CLUSTER_NAMES[0],
        KUBERNETES_CLUSTER_IDS[0],
    )
    load_namespaces(
        neo4j_session,
        KUBERNETES_CLUSTER_2_NAMESPACES_DATA,
        TEST_UPDATE_TAG,
        KUBERNETES_CLUSTER_NAMES[1],
        KUBERNETES_CLUSTER_IDS[1],
    )

    yield

    # Clean up
    neo4j_session.run(
        """
        MATCH (n: KubernetesNamespace)
        DETACH DELETE n
        """,
    )
    neo4j_session.run(
        """
        MATCH (n: KubernetesCluster)
        DETACH DELETE n
        """,
    )


def test_load_pods(neo4j_session, _create_test_cluster):
    # Act
    load_pods(
        neo4j_session,
        KUBERNETES_PODS_DATA,
        update_tag=TEST_UPDATE_TAG,
        cluster_id=KUBERNETES_CLUSTER_IDS[0],
        cluster_name=KUBERNETES_CLUSTER_NAMES[0],
    )

    # Assert
    expected_nodes = {("my-pod",), ("my-service-pod",)}
    assert check_nodes(neo4j_session, "KubernetesPod", ["name"]) == expected_nodes


def test_load_pod_relationships(neo4j_session, _create_test_cluster):
    # Act
    load_pods(
        neo4j_session,
        KUBERNETES_PODS_DATA,
        update_tag=TEST_UPDATE_TAG,
        cluster_id=KUBERNETES_CLUSTER_IDS[0],
        cluster_name=KUBERNETES_CLUSTER_NAMES[0],
    )

    # Assert: Expect pods to be in the correct namespace
    expected_rels = {
        ("my-namespace", "my-pod"),
        ("my-namespace", "my-service-pod"),
    }
    assert (
        check_rels(
            neo4j_session,
            "KubernetesNamespace",
            "name",
            "KubernetesPod",
            "name",
            "CONTAINS",
        )
        == expected_rels
    )

    # Assert: Expect pods to be in the correct namespace in the correct cluster
    expected_rels = {
        (KUBERNETES_CLUSTER_NAMES[0], "my-pod"),
        (KUBERNETES_CLUSTER_NAMES[0], "my-service-pod"),
    }
    assert (
        check_rels(
            neo4j_session,
            "KubernetesNamespace",
            "cluster_name",
            "KubernetesPod",
            "name",
            "CONTAINS",
        )
        == expected_rels
    )


def test_load_pod_containers(neo4j_session, _create_test_cluster):
    # Arrange
    load_pods(
        neo4j_session,
        KUBERNETES_PODS_DATA,
        update_tag=TEST_UPDATE_TAG,
        cluster_id=KUBERNETES_CLUSTER_IDS[0],
        cluster_name=KUBERNETES_CLUSTER_NAMES[0],
    )

    # Act
    load_containers(
        neo4j_session,
        KUBERNETES_CONTAINER_DATA,
        update_tag=TEST_UPDATE_TAG,
        cluster_id=KUBERNETES_CLUSTER_IDS[0],
        cluster_name=KUBERNETES_CLUSTER_NAMES[0],
    )

    # Assert
    expected_nodes = {("my-pod-container",), ("my-service-pod-container",)}
    assert check_nodes(neo4j_session, "KubernetesContainer", ["name"]) == expected_nodes


def test_load_pod_containers_relationships(neo4j_session, _create_test_cluster):
    # Arrange
    load_pods(
        neo4j_session,
        KUBERNETES_PODS_DATA,
        update_tag=TEST_UPDATE_TAG,
        cluster_id=KUBERNETES_CLUSTER_IDS[0],
        cluster_name=KUBERNETES_CLUSTER_NAMES[0],
    )

    # Act
    load_containers(
        neo4j_session,
        KUBERNETES_CONTAINER_DATA,
        update_tag=TEST_UPDATE_TAG,
        cluster_id=KUBERNETES_CLUSTER_IDS[0],
        cluster_name=KUBERNETES_CLUSTER_NAMES[0],
    )

    # Assert: Expect containers to be in the correct pod
    expected_rels = {
        ("my-pod", "my-pod-container"),
        ("my-service-pod", "my-service-pod-container"),
    }
    assert (
        check_rels(
            neo4j_session,
            "KubernetesPod",
            "name",
            "KubernetesContainer",
            "name",
            "CONTAINS",
        )
        == expected_rels
    )

    # Assert: Expect containers to be in the correct pod in the correct cluster
    expected_rels = {
        (KUBERNETES_CLUSTER_NAMES[0], "my-pod-container"),
        (KUBERNETES_CLUSTER_NAMES[0], "my-service-pod-container"),
    }
    assert (
        check_rels(
            neo4j_session,
            "KubernetesPod",
            "cluster_name",
            "KubernetesContainer",
            "name",
            "CONTAINS",
        )
        == expected_rels
    )


def test_pod_cleanup(neo4j_session, _create_test_cluster):
    # Arrange
    load_pods(
        neo4j_session,
        KUBERNETES_PODS_DATA,
        update_tag=TEST_UPDATE_TAG,
        cluster_id=KUBERNETES_CLUSTER_IDS[0],
        cluster_name=KUBERNETES_CLUSTER_NAMES[0],
    )

    load_containers(
        neo4j_session,
        KUBERNETES_CONTAINER_DATA,
        update_tag=TEST_UPDATE_TAG,
        cluster_id=KUBERNETES_CLUSTER_IDS[0],
        cluster_name=KUBERNETES_CLUSTER_NAMES[0],
    )

    # Act
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG + 1,
        "CLUSTER_ID": KUBERNETES_CLUSTER_IDS[0],
    }
    cleanup(neo4j_session, common_job_parameters)

    # Assert: Expect that the pods were deleted
    assert check_nodes(neo4j_session, "KubernetesPod", ["name"]) == set()
    assert check_nodes(neo4j_session, "KubernetesContainer", ["name"]) == set()


def test_load_container_resources(neo4j_session, _create_test_cluster):
    # Arrange
    load_pods(
        neo4j_session,
        KUBERNETES_PODS_DATA,
        update_tag=TEST_UPDATE_TAG,
        cluster_id=KUBERNETES_CLUSTER_IDS[0],
        cluster_name=KUBERNETES_CLUSTER_NAMES[0],
    )

    # Act
    load_containers(
        neo4j_session,
        KUBERNETES_CONTAINER_DATA,
        update_tag=TEST_UPDATE_TAG,
        cluster_id=KUBERNETES_CLUSTER_IDS[0],
        cluster_name=KUBERNETES_CLUSTER_NAMES[0],
    )

    # Assert: Verify that resource fields are stored correctly for my-pod-container
    expected_nodes = {("my-pod-container", "128Mi", "100m", "256Mi", "500m")}
    assert (
        check_nodes(
            neo4j_session,
            "KubernetesContainer",
            ["name", "memory_request", "cpu_request", "memory_limit", "cpu_limit"],
        )
        >= expected_nodes
    )

    # Assert: Verify resource fields for my-service-pod-container
    expected_nodes = {("my-service-pod-container", "64Mi", "50m", "128Mi", "200m")}
    assert (
        check_nodes(
            neo4j_session,
            "KubernetesContainer",
            ["name", "memory_request", "cpu_request", "memory_limit", "cpu_limit"],
        )
        >= expected_nodes
    )
