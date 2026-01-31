import pytest

from cartography.intel.kubernetes.clusters import load_kubernetes_cluster
from cartography.intel.kubernetes.ingress import cleanup
from cartography.intel.kubernetes.ingress import load_ingresses
from cartography.intel.kubernetes.namespaces import load_namespaces
from cartography.intel.kubernetes.services import load_services
from tests.data.kubernetes.clusters import KUBERNETES_CLUSTER_DATA
from tests.data.kubernetes.clusters import KUBERNETES_CLUSTER_IDS
from tests.data.kubernetes.clusters import KUBERNETES_CLUSTER_NAMES
from tests.data.kubernetes.ingress import KUBERNETES_ALB_INGRESS_DATA
from tests.data.kubernetes.ingress import KUBERNETES_INGRESS_DATA
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
