from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

import cartography.intel.kubernetes.ingress
from cartography.intel.aws.ec2.load_balancer_v2s import load_load_balancer_v2s
from cartography.intel.kubernetes.clusters import load_kubernetes_cluster
from cartography.intel.kubernetes.ingress import cleanup
from cartography.intel.kubernetes.ingress import load_ingresses
from cartography.intel.kubernetes.ingress import sync_ingress
from cartography.intel.kubernetes.namespaces import load_namespaces
from cartography.intel.kubernetes.services import load_services
from tests.data.aws.ec2.load_balancer_v2s import GET_LOAD_BALANCER_V2_DATA
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
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_ACCOUNT_ID = "000000000000"
TEST_REGION = "us-east-1"


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
    neo4j_session.run(
        """
        MATCH (n: AWSLoadBalancerV2)
        DETACH DELETE n
        """,
    )
    neo4j_session.run(
        """
        MATCH (n: ELBV2Listener)
        DETACH DELETE n
        """,
    )
    neo4j_session.run(
        """
        MATCH (n: AWSAccount)
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


@patch.object(cartography.intel.kubernetes.ingress, "get_ingress")
def test_load_ingress_to_loadbalancer_relationship(
    mock_get_ingress,
    neo4j_session,
    _create_test_cluster,
):
    """
    Test that KubernetesIngress creates USES_LOAD_BALANCER relationship to
    AWSLoadBalancerV2 when the DNS names match.
    """
    # Arrange: Mock get_ingress with raw ALB ingress objects
    mock_get_ingress.return_value = KUBERNETES_ALB_INGRESS_RAW

    # Arrange: Create AWS Account and LoadBalancerV2 nodes using the real loader
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)
    load_load_balancer_v2s(
        neo4j_session,
        GET_LOAD_BALANCER_V2_DATA,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    # Act: Run sync_ingress (the production entry point)
    k8s_client = MagicMock()
    k8s_client.name = KUBERNETES_CLUSTER_NAMES[0]
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "CLUSTER_ID": KUBERNETES_CLUSTER_IDS[0],
    }
    sync_ingress(
        neo4j_session=neo4j_session,
        client=k8s_client,
        update_tag=TEST_UPDATE_TAG,
        common_job_parameters=common_job_parameters,
    )

    # Assert: Expect USES_LOAD_BALANCER relationships exist
    expected_rels = {
        ("alb-ingress-api", SHARED_ALB_DNS_NAME),
        ("alb-ingress-web", SHARED_ALB_DNS_NAME),
    }
    assert (
        check_rels(
            neo4j_session,
            "KubernetesIngress",
            "name",
            "AWSLoadBalancerV2",
            "dnsname",
            "USES_LOAD_BALANCER",
            rel_direction_right=True,
        )
        == expected_rels
    )


@patch.object(cartography.intel.kubernetes.ingress, "get_ingress")
def test_load_ingress_no_loadbalancer_relationship_when_no_match(
    mock_get_ingress,
    neo4j_session,
    _create_test_cluster,
):
    """
    Test that KubernetesIngress does NOT create USES_LOAD_BALANCER relationship
    when there is no matching AWS LoadBalancerV2.
    """
    # Arrange: Mock get_ingress with raw ingress objects (no LB DNS names)
    mock_get_ingress.return_value = KUBERNETES_INGRESS_RAW

    # Arrange: Create AWS Account and LoadBalancerV2 nodes using the real loader
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)
    load_load_balancer_v2s(
        neo4j_session,
        GET_LOAD_BALANCER_V2_DATA,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    # Act: Run sync_ingress (the production entry point)
    k8s_client = MagicMock()
    k8s_client.name = KUBERNETES_CLUSTER_NAMES[0]
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "CLUSTER_ID": KUBERNETES_CLUSTER_IDS[0],
    }
    sync_ingress(
        neo4j_session=neo4j_session,
        client=k8s_client,
        update_tag=TEST_UPDATE_TAG,
        common_job_parameters=common_job_parameters,
    )

    # Assert: Expect that the ingresses were loaded
    expected_nodes = {("my-ingress",), ("simple-ingress",)}
    assert check_nodes(neo4j_session, "KubernetesIngress", ["name"]) == expected_nodes

    # Assert: No USES_LOAD_BALANCER relationship should exist (DNS names don't match)
    assert (
        check_rels(
            neo4j_session,
            "KubernetesIngress",
            "name",
            "AWSLoadBalancerV2",
            "dnsname",
            "USES_LOAD_BALANCER",
            rel_direction_right=True,
        )
        == set()
    )
