import pytest

from cartography.intel.kubernetes.clusters import load_kubernetes_cluster
from cartography.intel.kubernetes.ingress import cleanup
from cartography.intel.kubernetes.ingress import load_ingresses
from cartography.intel.kubernetes.namespaces import load_namespaces
from cartography.intel.kubernetes.services import load_services
from tests.data.kubernetes.clusters import KUBERNETES_CLUSTER_DATA
from tests.data.kubernetes.clusters import KUBERNETES_CLUSTER_IDS
from tests.data.kubernetes.clusters import KUBERNETES_CLUSTER_NAMES
from tests.data.kubernetes.ingress import KUBERNETES_INGRESS_DATA
from tests.data.kubernetes.namespaces import KUBERNETES_CLUSTER_1_NAMESPACES_DATA
from tests.data.kubernetes.namespaces import KUBERNETES_CLUSTER_2_NAMESPACES_DATA
from tests.data.kubernetes.services import KUBERNETES_SERVICES_DATA
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
    load_namespaces(
        neo4j_session,
        KUBERNETES_CLUSTER_1_NAMESPACES_DATA,
        update_tag=TEST_UPDATE_TAG,
        cluster_id=KUBERNETES_CLUSTER_IDS[0],
        cluster_name=KUBERNETES_CLUSTER_NAMES[0],
    )
    load_namespaces(
        neo4j_session,
        KUBERNETES_CLUSTER_2_NAMESPACES_DATA,
        update_tag=TEST_UPDATE_TAG,
        cluster_id=KUBERNETES_CLUSTER_IDS[1],
        cluster_name=KUBERNETES_CLUSTER_NAMES[1],
    )

    yield


def test_load_ingresses(neo4j_session, _create_test_cluster):
    # Act
    load_ingresses(
        neo4j_session,
        KUBERNETES_INGRESS_DATA,
        update_tag=TEST_UPDATE_TAG,
        cluster_id=KUBERNETES_CLUSTER_IDS[0],
        cluster_name=KUBERNETES_CLUSTER_NAMES[0],
    )

    # Assert: Expect that the ingresses were loaded
    expected_nodes = {("my-ingress",), ("simple-ingress",)}
    assert check_nodes(neo4j_session, "KubernetesIngress", ["name"]) == expected_nodes


def test_load_ingress_to_namespace_relationship(neo4j_session, _create_test_cluster):
    # Act
    load_ingresses(
        neo4j_session,
        KUBERNETES_INGRESS_DATA,
        update_tag=TEST_UPDATE_TAG,
        cluster_id=KUBERNETES_CLUSTER_IDS[0],
        cluster_name=KUBERNETES_CLUSTER_NAMES[0],
    )

    # Assert: Expect ingresses to be in the correct namespace
    expected_rels = {
        (KUBERNETES_CLUSTER_1_NAMESPACES_DATA[-1]["name"], "my-ingress"),
        (KUBERNETES_CLUSTER_1_NAMESPACES_DATA[-1]["name"], "simple-ingress"),
    }
    assert (
        check_rels(
            neo4j_session,
            "KubernetesNamespace",
            "name",
            "KubernetesIngress",
            "name",
            "CONTAINS",
        )
        == expected_rels
    )


def test_load_ingress_to_cluster_relationship(neo4j_session, _create_test_cluster):
    # Act
    load_ingresses(
        neo4j_session,
        KUBERNETES_INGRESS_DATA,
        update_tag=TEST_UPDATE_TAG,
        cluster_id=KUBERNETES_CLUSTER_IDS[0],
        cluster_name=KUBERNETES_CLUSTER_NAMES[0],
    )

    # Assert: Expect ingresses to be in the correct cluster
    expected_rels = {
        (KUBERNETES_CLUSTER_IDS[0], "my-ingress"),
        (KUBERNETES_CLUSTER_IDS[0], "simple-ingress"),
    }
    assert (
        check_rels(
            neo4j_session,
            "KubernetesCluster",
            "id",
            "KubernetesIngress",
            "name",
            "RESOURCE",
        )
        == expected_rels
    )


def test_load_ingress_to_service_relationship(neo4j_session, _create_test_cluster):
    # Arrange: Load services first
    load_services(
        neo4j_session,
        KUBERNETES_SERVICES_DATA,
        update_tag=TEST_UPDATE_TAG,
        cluster_id=KUBERNETES_CLUSTER_IDS[0],
        cluster_name=KUBERNETES_CLUSTER_NAMES[0],
    )

    # Act: Load ingresses
    load_ingresses(
        neo4j_session,
        KUBERNETES_INGRESS_DATA,
        update_tag=TEST_UPDATE_TAG,
        cluster_id=KUBERNETES_CLUSTER_IDS[0],
        cluster_name=KUBERNETES_CLUSTER_NAMES[0],
    )

    # Assert: Expect ingresses to target the correct services
    expected_rels = {
        ("my-ingress", "api-service"),
        ("my-ingress", "app-service"),
        ("simple-ingress", "simple-service"),
    }
    assert (
        check_rels(
            neo4j_session,
            "KubernetesIngress",
            "name",
            "KubernetesService",
            "name",
            "TARGETS",
        )
        == expected_rels
    )


def test_ingress_cleanup(neo4j_session, _create_test_cluster):
    # Arrange
    load_ingresses(
        neo4j_session,
        KUBERNETES_INGRESS_DATA,
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

    # Assert: Expect that the ingresses were deleted
    assert check_nodes(neo4j_session, "KubernetesIngress", ["name"]) == set()
