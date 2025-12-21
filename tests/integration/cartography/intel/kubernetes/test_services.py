import pytest

import cartography.intel.aws.ec2.load_balancer_v2s
from cartography.intel.kubernetes.clusters import load_kubernetes_cluster
from cartography.intel.kubernetes.namespaces import load_namespaces
from cartography.intel.kubernetes.pods import load_pods
from cartography.intel.kubernetes.services import cleanup
from cartography.intel.kubernetes.services import load_services
from tests.data.aws.ec2.load_balancers import LOAD_BALANCER_DATA
from tests.data.kubernetes.clusters import KUBERNETES_CLUSTER_DATA
from tests.data.kubernetes.clusters import KUBERNETES_CLUSTER_IDS
from tests.data.kubernetes.clusters import KUBERNETES_CLUSTER_NAMES
from tests.data.kubernetes.namespaces import KUBERNETES_CLUSTER_1_NAMESPACES_DATA
from tests.data.kubernetes.namespaces import KUBERNETES_CLUSTER_2_NAMESPACES_DATA
from tests.data.kubernetes.pods import KUBERNETES_PODS_DATA
from tests.data.kubernetes.services import AWS_TEST_LB_DNS_NAME
from tests.data.kubernetes.services import AWS_TEST_LB_DNS_NAME_2
from tests.data.kubernetes.services import KUBERNETES_LOADBALANCER_SERVICE_DATA
from tests.data.kubernetes.services import KUBERNETES_MULTI_LB_SERVICE_DATA
from tests.data.kubernetes.services import KUBERNETES_SERVICES_DATA
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


def test_load_services_with_aws_loadbalancer_relationship(
    neo4j_session, _create_test_cluster
):
    """
    Test that KubernetesService of type LoadBalancer creates USES_LOAD_BALANCER
    relationship to AWS LoadBalancerV2 when the DNS names match.

    Uses the actual AWS LoadBalancerV2 test data and sync function to ensure
    this test stays in sync if the AWS LB schema changes.
    """
    # Arrange: Create prerequisite AWS resources and load the LoadBalancerV2
    neo4j_session.run(
        """
        MERGE (aws:AWSAccount{id: $aws_account_id})
        ON CREATE SET aws.firstseen = timestamp()
        SET aws.lastupdated = $update_tag
        """,
        aws_account_id=TEST_ACCOUNT_ID,
        update_tag=TEST_UPDATE_TAG,
    )

    # Load AWS LoadBalancerV2 using the actual sync function and test data
    cartography.intel.aws.ec2.load_balancer_v2s.load_load_balancer_v2s(
        neo4j_session,
        LOAD_BALANCER_DATA,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    # Act: Load the LoadBalancer type Kubernetes service
    load_services(
        neo4j_session,
        KUBERNETES_LOADBALANCER_SERVICE_DATA,
        update_tag=TEST_UPDATE_TAG,
        cluster_id=KUBERNETES_CLUSTER_IDS[0],
        cluster_name=KUBERNETES_CLUSTER_NAMES[0],
    )

    # Assert: Expect that the service was loaded
    expected_nodes = {("my-lb-service",)}
    assert check_nodes(neo4j_session, "KubernetesService", ["name"]) == expected_nodes

    # Assert: Expect USES_LOAD_BALANCER relationship exists
    # AWS_TEST_LB_DNS_NAME is derived from LOAD_BALANCER_DATA to keep tests in sync
    expected_rels = {
        ("my-lb-service", AWS_TEST_LB_DNS_NAME),
    }
    assert (
        check_rels(
            neo4j_session,
            "KubernetesService",
            "name",
            "LoadBalancerV2",
            "dnsname",
            "USES_LOAD_BALANCER",
            rel_direction_right=True,
        )
        == expected_rels
    )


def test_load_services_no_loadbalancer_relationship_when_no_match(
    neo4j_session, _create_test_cluster
):
    """
    Test that KubernetesService of type LoadBalancer does NOT create USES_LOAD_BALANCER
    relationship when there is no matching AWS LoadBalancerV2.
    """
    # Clean up any LoadBalancerV2 nodes from previous tests
    neo4j_session.run("MATCH (lb:LoadBalancerV2) DETACH DELETE lb")

    # Arrange: Create an AWS LoadBalancerV2 node with NON-matching DNS name
    neo4j_session.run(
        """
        MERGE (lb:LoadBalancerV2{id: 'different-lb.elb.us-east-1.amazonaws.com',
                                  dnsname: 'different-lb.elb.us-east-1.amazonaws.com'})
        ON CREATE SET lb.firstseen = timestamp()
        SET lb.lastupdated = $update_tag
        """,
        update_tag=TEST_UPDATE_TAG,
    )

    # Act: Load the LoadBalancer type Kubernetes service
    load_services(
        neo4j_session,
        KUBERNETES_LOADBALANCER_SERVICE_DATA,
        update_tag=TEST_UPDATE_TAG,
        cluster_id=KUBERNETES_CLUSTER_IDS[0],
        cluster_name=KUBERNETES_CLUSTER_NAMES[0],
    )

    # Assert: Expect that the service was loaded
    expected_nodes = {("my-lb-service",)}
    assert check_nodes(neo4j_session, "KubernetesService", ["name"]) == expected_nodes

    # Assert: No USES_LOAD_BALANCER relationship should exist (DNS names don't match)
    assert (
        check_rels(
            neo4j_session,
            "KubernetesService",
            "name",
            "LoadBalancerV2",
            "dnsname",
            "USES_LOAD_BALANCER",
            rel_direction_right=True,
        )
        == set()
    )


def test_load_services_multiple_dns_names_creates_multiple_relationships(
    neo4j_session, _create_test_cluster
):
    """
    Test one-to-many: a single KubernetesService with multiple DNS names
    creates USES_LOAD_BALANCER relationships to multiple LoadBalancerV2 nodes.

    Real-world scenario: AWS frontend NLB feature where a service gets both
    NLB and ALB DNS entries in status.loadBalancer.ingress[].
    """
    # Clean up from previous tests
    neo4j_session.run("MATCH (s:KubernetesService) DETACH DELETE s")
    neo4j_session.run("MATCH (lb:LoadBalancerV2) DETACH DELETE lb")

    # Arrange: Create two LoadBalancerV2 nodes with different DNS names
    neo4j_session.run(
        """
        MERGE (aws:AWSAccount{id: $aws_account_id})
        ON CREATE SET aws.firstseen = timestamp()
        SET aws.lastupdated = $update_tag
        """,
        aws_account_id=TEST_ACCOUNT_ID,
        update_tag=TEST_UPDATE_TAG,
    )

    # Load first LB using actual sync function
    cartography.intel.aws.ec2.load_balancer_v2s.load_load_balancer_v2s(
        neo4j_session,
        LOAD_BALANCER_DATA,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    # Create second LB manually (simulating a second NLB/ALB)
    neo4j_session.run(
        """
        MERGE (lb:LoadBalancerV2{id: $dns_name, dnsname: $dns_name})
        ON CREATE SET lb.firstseen = timestamp()
        SET lb.lastupdated = $update_tag, lb.name = 'second-lb'
        """,
        dns_name=AWS_TEST_LB_DNS_NAME_2,
        update_tag=TEST_UPDATE_TAG,
    )

    # Act: Load service with multiple DNS names
    load_services(
        neo4j_session,
        KUBERNETES_MULTI_LB_SERVICE_DATA,
        update_tag=TEST_UPDATE_TAG,
        cluster_id=KUBERNETES_CLUSTER_IDS[0],
        cluster_name=KUBERNETES_CLUSTER_NAMES[0],
    )

    # Assert: Both relationships should exist
    expected_rels = {
        ("multi-lb-service", AWS_TEST_LB_DNS_NAME),
        ("multi-lb-service", AWS_TEST_LB_DNS_NAME_2),
    }
    assert (
        check_rels(
            neo4j_session,
            "KubernetesService",
            "name",
            "LoadBalancerV2",
            "dnsname",
            "USES_LOAD_BALANCER",
            rel_direction_right=True,
        )
        == expected_rels
    )


def test_clusterip_service_does_not_create_loadbalancer_relationship(
    neo4j_session, _create_test_cluster
):
    """
    Test that ClusterIP services do NOT create USES_LOAD_BALANCER relationships,
    even when LoadBalancerV2 nodes exist in the graph.

    Only services of type LoadBalancer should create this relationship.
    """
    # Clean up from previous tests
    neo4j_session.run("MATCH (s:KubernetesService) DETACH DELETE s")
    neo4j_session.run("MATCH (lb:LoadBalancerV2) DETACH DELETE lb")

    # Arrange: Create a LoadBalancerV2 node
    neo4j_session.run(
        """
        MERGE (aws:AWSAccount{id: $aws_account_id})
        ON CREATE SET aws.firstseen = timestamp()
        SET aws.lastupdated = $update_tag
        """,
        aws_account_id=TEST_ACCOUNT_ID,
        update_tag=TEST_UPDATE_TAG,
    )

    cartography.intel.aws.ec2.load_balancer_v2s.load_load_balancer_v2s(
        neo4j_session,
        LOAD_BALANCER_DATA,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    # Act: Load ClusterIP service (KUBERNETES_SERVICES_DATA has type: ClusterIP)
    load_services(
        neo4j_session,
        KUBERNETES_SERVICES_DATA,
        update_tag=TEST_UPDATE_TAG,
        cluster_id=KUBERNETES_CLUSTER_IDS[0],
        cluster_name=KUBERNETES_CLUSTER_NAMES[0],
    )

    # Assert: Service was loaded
    assert check_nodes(neo4j_session, "KubernetesService", ["name"]) == {
        ("my-service",)
    }

    # Assert: No USES_LOAD_BALANCER relationship (ClusterIP services don't have load_balancer_dns_names)
    assert (
        check_rels(
            neo4j_session,
            "KubernetesService",
            "name",
            "LoadBalancerV2",
            "dnsname",
            "USES_LOAD_BALANCER",
            rel_direction_right=True,
        )
        == set()
    )
