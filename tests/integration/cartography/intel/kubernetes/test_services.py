import pytest

from cartography.intel.kubernetes.clusters import load_kubernetes_cluster
from cartography.intel.kubernetes.namespaces import load_namespaces
from cartography.intel.kubernetes.pods import load_pods
from cartography.intel.kubernetes.services import cleanup
from cartography.intel.kubernetes.services import load_services
from tests.data.kubernetes.clusters import KUBERNETES_CLUSTER_DATA
from tests.data.kubernetes.clusters import KUBERNETES_CLUSTER_IDS
from tests.data.kubernetes.clusters import KUBERNETES_CLUSTER_NAMES
from tests.data.kubernetes.namespaces import KUBERNETES_CLUSTER_1_NAMESPACES_DATA
from tests.data.kubernetes.namespaces import KUBERNETES_CLUSTER_2_NAMESPACES_DATA
from tests.data.kubernetes.pods import KUBERNETES_PODS_DATA
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
    load_pods(
        neo4j_session,
        KUBERNETES_PODS_DATA,
        update_tag=TEST_UPDATE_TAG,
        cluster_id=KUBERNETES_CLUSTER_IDS[0],
        cluster_name=KUBERNETES_CLUSTER_NAMES[0],
    )

    yield


def test_load_services(neo4j_session, _create_test_cluster):
    # Act
    load_services(
        neo4j_session,
        KUBERNETES_SERVICES_DATA,
        update_tag=TEST_UPDATE_TAG,
        cluster_id=KUBERNETES_CLUSTER_IDS[0],
        cluster_name=KUBERNETES_CLUSTER_NAMES[0],
    )

    # Assert: Expect that the services were loaded
    expected_nodes = {("my-service",)}
    assert check_nodes(neo4j_session, "KubernetesService", ["name"]) == expected_nodes


def test_load_services_relationships(neo4j_session, _create_test_cluster):
    # Act
    load_services(
        neo4j_session,
        KUBERNETES_SERVICES_DATA,
        update_tag=TEST_UPDATE_TAG,
        cluster_id=KUBERNETES_CLUSTER_IDS[0],
        cluster_name=KUBERNETES_CLUSTER_NAMES[0],
    )

    # Assert: Expect services to be in the correct namespace
    expected_rels = {
        (KUBERNETES_CLUSTER_1_NAMESPACES_DATA[-1]["name"], "my-service"),
    }
    assert (
        check_rels(
            neo4j_session,
            "KubernetesNamespace",
            "name",
            "KubernetesService",
            "name",
            "CONTAINS",
        )
        == expected_rels
    )

    # Assert: Expect services to be in the correct cluster
    expected_rels = {
        (KUBERNETES_CLUSTER_NAMES[0], "my-service"),
    }
    assert (
        check_rels(
            neo4j_session,
            "KubernetesNamespace",
            "cluster_name",
            "KubernetesService",
            "name",
            "CONTAINS",
        )
        == expected_rels
    )


def test_service_cleanup(neo4j_session, _create_test_cluster):
    # Arrange
    load_services(
        neo4j_session,
        KUBERNETES_SERVICES_DATA,
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

    # Assert: Expect that the services were deleted
    assert check_nodes(neo4j_session, "KubernetesService", ["name"]) == set()
