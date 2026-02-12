from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

import cartography.intel.kubernetes.ingress
from cartography.intel.kubernetes.clusters import load_kubernetes_cluster
from cartography.intel.kubernetes.ingress import cleanup
from cartography.intel.kubernetes.ingress import load_ingresses
from cartography.intel.kubernetes.ingress import sync_ingress
from cartography.intel.kubernetes.namespaces import load_namespaces
from cartography.intel.kubernetes.services import load_services
from tests.data.kubernetes.clusters import KUBERNETES_CLUSTER_DATA
from tests.data.kubernetes.clusters import KUBERNETES_CLUSTER_IDS
from tests.data.kubernetes.clusters import KUBERNETES_CLUSTER_NAMES
from tests.data.kubernetes.ingress import KUBERNETES_ALB_INGRESS_DATA
from tests.data.kubernetes.ingress import KUBERNETES_ALB_INGRESS_RAW
from tests.data.kubernetes.ingress import KUBERNETES_INGRESS_DATA
from tests.data.kubernetes.ingress import KUBERNETES_INGRESS_RAW
from tests.data.kubernetes.ingress import SHARED_ALB_DNS_NAME
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
    load_services(
        neo4j_session,
        KUBERNETES_SERVICES_DATA,
        update_tag=TEST_UPDATE_TAG,
        cluster_id=KUBERNETES_CLUSTER_IDS[0],
        cluster_name=KUBERNETES_CLUSTER_NAMES[0],
    )

    yield

    neo4j_session.run(
        """
        MATCH (n: KubernetesIngress)
        DETACH DELETE n
        """,
    )
    neo4j_session.run(
        """
        MATCH (n: KubernetesService)
        DETACH DELETE n
        """,
    )
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


def test_load_alb_ingresses_with_ingress_group(neo4j_session, _create_test_cluster):
    """Test that AWS ALB ingresses with ingress group annotations are loaded correctly."""
    # Act
    load_ingresses(
        neo4j_session,
        KUBERNETES_ALB_INGRESS_DATA,
        update_tag=TEST_UPDATE_TAG,
        cluster_id=KUBERNETES_CLUSTER_IDS[0],
        cluster_name=KUBERNETES_CLUSTER_NAMES[0],
    )

    # Assert: Expect that the ALB ingresses were loaded with correct properties
    expected_nodes = {
        ("alb-ingress-api", "shared-alb"),
        ("alb-ingress-web", "shared-alb"),
    }
    assert (
        check_nodes(neo4j_session, "KubernetesIngress", ["name", "ingress_group_name"])
        == expected_nodes
    )


def test_load_alb_ingresses_load_balancer_dns_names(
    neo4j_session, _create_test_cluster
):
    """Test that load balancer DNS names are stored correctly on ingresses."""
    # Act
    load_ingresses(
        neo4j_session,
        KUBERNETES_ALB_INGRESS_DATA,
        update_tag=TEST_UPDATE_TAG,
        cluster_id=KUBERNETES_CLUSTER_IDS[0],
        cluster_name=KUBERNETES_CLUSTER_NAMES[0],
    )

    # Assert: Check that load_balancer_dns_names is set correctly
    result = neo4j_session.run(
        """
        MATCH (i:KubernetesIngress)
        WHERE i.ingress_group_name = 'shared-alb'
        RETURN i.name as name, i.load_balancer_dns_names as dns_names
        ORDER BY i.name
        """
    )
    records = list(result)

    assert len(records) == 2
    # Both ingresses in the same group should have the same ALB DNS name
    for record in records:
        assert SHARED_ALB_DNS_NAME in record["dns_names"]


def test_load_ingresses_without_ingress_group(neo4j_session, _create_test_cluster):
    """Test that ingresses without ingress group have null ingress_group_name."""
    # Act
    load_ingresses(
        neo4j_session,
        KUBERNETES_INGRESS_DATA,
        update_tag=TEST_UPDATE_TAG,
        cluster_id=KUBERNETES_CLUSTER_IDS[0],
        cluster_name=KUBERNETES_CLUSTER_NAMES[0],
    )

    # Assert: Expect ingresses without ALB annotation to have null ingress_group_name
    result = neo4j_session.run(
        """
        MATCH (i:KubernetesIngress)
        WHERE i.name IN ['my-ingress', 'simple-ingress']
        RETURN i.name as name, i.ingress_group_name as group_name
        ORDER BY i.name
        """
    )
    records = list(result)

    assert len(records) == 2
    for record in records:
        assert record["group_name"] is None


@patch.object(cartography.intel.kubernetes.ingress, "get_ingress")
def test_sync_ingress_end_to_end(mock_get_ingress, neo4j_session, _create_test_cluster):
    """
    Test the complete end-to-end ingress sync flow.
    """
    # Arrange: Mock get_ingress with raw Kubernetes API objects
    mock_get_ingress.return_value = KUBERNETES_INGRESS_RAW

    # Create a mock K8s client
    k8s_client = MagicMock()
    k8s_client.name = KUBERNETES_CLUSTER_NAMES[0]

    # Define common job parameters
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "CLUSTER_ID": KUBERNETES_CLUSTER_IDS[0],
    }

    # Act: Run the complete sync
    sync_ingress(
        neo4j_session=neo4j_session,
        client=k8s_client,
        update_tag=TEST_UPDATE_TAG,
        common_job_parameters=common_job_parameters,
    )

    # Assert: Verify get_ingress was called with the client
    mock_get_ingress.assert_called_once_with(k8s_client)

    # Assert: Verify Ingress nodes were created
    expected_ingress_nodes = {
        ("my-ingress", "nginx"),
        ("simple-ingress", "nginx"),
    }
    actual_ingress_nodes = check_nodes(
        neo4j_session, "KubernetesIngress", ["name", "ingress_class_name"]
    )
    assert actual_ingress_nodes == expected_ingress_nodes

    # Assert: Verify Ingress to Cluster relationships
    expected_ingress_to_cluster = {
        (KUBERNETES_CLUSTER_IDS[0], "my-ingress"),
        (KUBERNETES_CLUSTER_IDS[0], "simple-ingress"),
    }
    actual_ingress_to_cluster = check_rels(
        neo4j_session,
        "KubernetesCluster",
        "id",
        "KubernetesIngress",
        "name",
        "RESOURCE",
    )
    assert actual_ingress_to_cluster == expected_ingress_to_cluster

    # Assert: Verify Ingress to Namespace relationships
    expected_ingress_to_namespace = {
        (KUBERNETES_CLUSTER_1_NAMESPACES_DATA[-1]["name"], "my-ingress"),
        (KUBERNETES_CLUSTER_1_NAMESPACES_DATA[-1]["name"], "simple-ingress"),
    }
    actual_ingress_to_namespace = check_rels(
        neo4j_session,
        "KubernetesNamespace",
        "name",
        "KubernetesIngress",
        "name",
        "CONTAINS",
    )
    assert actual_ingress_to_namespace == expected_ingress_to_namespace

    # Assert: Verify Ingress to Service relationships (TARGETS)
    expected_ingress_to_service = {
        ("my-ingress", "api-service"),
        ("my-ingress", "app-service"),
        ("simple-ingress", "simple-service"),
    }
    actual_ingress_to_service = check_rels(
        neo4j_session,
        "KubernetesIngress",
        "name",
        "KubernetesService",
        "name",
        "TARGETS",
    )
    assert actual_ingress_to_service == expected_ingress_to_service

    # Test ALB ingresses with load balancer DNS names
    mock_get_ingress.return_value = KUBERNETES_ALB_INGRESS_RAW
    common_job_parameters["UPDATE_TAG"] = TEST_UPDATE_TAG + 1

    sync_ingress(
        neo4j_session=neo4j_session,
        client=k8s_client,
        update_tag=TEST_UPDATE_TAG + 1,
        common_job_parameters=common_job_parameters,
    )

    # Assert: Verify ALB ingresses were created with correct properties
    expected_alb_ingress_nodes = {
        ("alb-ingress-api", "shared-alb", "alb"),
        ("alb-ingress-web", "shared-alb", "alb"),
    }
    actual_alb_ingress_nodes = check_nodes(
        neo4j_session,
        "KubernetesIngress",
        ["name", "ingress_group_name", "ingress_class_name"],
    )
    assert actual_alb_ingress_nodes == expected_alb_ingress_nodes

    # Assert: Verify old ingresses were removed
    final_ingress_nodes = check_nodes(neo4j_session, "KubernetesIngress", ["name"])
    assert final_ingress_nodes == {("alb-ingress-api",), ("alb-ingress-web",)}

    # Test empty response handling
    mock_get_ingress.return_value = []
    common_job_parameters["UPDATE_TAG"] = TEST_UPDATE_TAG + 2

    sync_ingress(
        neo4j_session=neo4j_session,
        client=k8s_client,
        update_tag=TEST_UPDATE_TAG + 2,
        common_job_parameters=common_job_parameters,
    )

    # Assert: All ingresses should be cleaned up
    ingress_nodes = check_nodes(neo4j_session, "KubernetesIngress", ["name"])
    assert set() == ingress_nodes
