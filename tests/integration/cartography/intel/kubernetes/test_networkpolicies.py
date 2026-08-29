import pytest

from cartography.intel.kubernetes.clusters import load_kubernetes_cluster
from cartography.intel.kubernetes.namespaces import load_namespaces
from cartography.intel.kubernetes.networkpolicies import cleanup
from cartography.intel.kubernetes.networkpolicies import load_network_policies
from cartography.intel.kubernetes.pods import load_pods
from tests.data.kubernetes.clusters import KUBERNETES_CLUSTER_DATA
from tests.data.kubernetes.clusters import KUBERNETES_CLUSTER_IDS
from tests.data.kubernetes.clusters import KUBERNETES_CLUSTER_NAMES
from tests.data.kubernetes.namespaces import KUBERNETES_CLUSTER_1_NAMESPACES_DATA
from tests.data.kubernetes.namespaces import KUBERNETES_CLUSTER_2_NAMESPACES_DATA
from tests.data.kubernetes.networkpolicies import KUBERNETES_NETWORK_POLICIES_DATA
from tests.data.kubernetes.pods import KUBERNETES_PODS_DATA
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


def test_load_network_policies(neo4j_session, _create_test_cluster):
    # Act
    load_network_policies(
        neo4j_session,
        KUBERNETES_NETWORK_POLICIES_DATA,
        update_tag=TEST_UPDATE_TAG,
        cluster_id=KUBERNETES_CLUSTER_IDS[0],
        cluster_name=KUBERNETES_CLUSTER_NAMES[0],
    )

    # Assert: nodes loaded with their restriction flags
    expected_nodes = {
        ("default-deny-ingress", True, False),
        ("allow-web-ingress", True, False),
        ("restrict-egress", False, True),
    }
    assert (
        check_nodes(
            neo4j_session,
            "KubernetesNetworkPolicy",
            ["name", "restricts_ingress", "restricts_egress"],
        )
        == expected_nodes
    )


def test_load_network_policies_relationships(neo4j_session, _create_test_cluster):
    # Act
    load_network_policies(
        neo4j_session,
        KUBERNETES_NETWORK_POLICIES_DATA,
        update_tag=TEST_UPDATE_TAG,
        cluster_id=KUBERNETES_CLUSTER_IDS[0],
        cluster_name=KUBERNETES_CLUSTER_NAMES[0],
    )

    # Assert: policies attached to their cluster
    expected_cluster_rels = {
        (KUBERNETES_CLUSTER_IDS[0], "default-deny-ingress"),
        (KUBERNETES_CLUSTER_IDS[0], "allow-web-ingress"),
        (KUBERNETES_CLUSTER_IDS[0], "restrict-egress"),
    }
    assert (
        check_rels(
            neo4j_session,
            "KubernetesCluster",
            "id",
            "KubernetesNetworkPolicy",
            "name",
            "RESOURCE",
        )
        == expected_cluster_rels
    )

    # Assert: policies contained by their namespace
    expected_ns_rels = {
        (KUBERNETES_CLUSTER_1_NAMESPACES_DATA[-1]["name"], "default-deny-ingress"),
        (KUBERNETES_CLUSTER_1_NAMESPACES_DATA[-1]["name"], "allow-web-ingress"),
        (KUBERNETES_CLUSTER_1_NAMESPACES_DATA[-1]["name"], "restrict-egress"),
    }
    assert (
        check_rels(
            neo4j_session,
            "KubernetesNamespace",
            "name",
            "KubernetesNetworkPolicy",
            "name",
            "CONTAINS",
        )
        == expected_ns_rels
    )

    # Assert: APPLIES_TO resolves podSelector to the right pods.
    # default-deny (empty selector) => both pods; label-scoped policies => one pod each.
    expected_pod_rels = {
        ("default-deny-ingress", KUBERNETES_PODS_DATA[0]["uid"]),
        ("default-deny-ingress", KUBERNETES_PODS_DATA[1]["uid"]),
        ("allow-web-ingress", KUBERNETES_PODS_DATA[0]["uid"]),
        ("restrict-egress", KUBERNETES_PODS_DATA[1]["uid"]),
    }
    assert (
        check_rels(
            neo4j_session,
            "KubernetesNetworkPolicy",
            "name",
            "KubernetesPod",
            "id",
            "APPLIES_TO",
            rel_direction_right=True,
        )
        == expected_pod_rels
    )


def test_network_policy_cleanup(neo4j_session, _create_test_cluster):
    # Arrange
    load_network_policies(
        neo4j_session,
        KUBERNETES_NETWORK_POLICIES_DATA,
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

    # Assert: policies were deleted
    assert check_nodes(neo4j_session, "KubernetesNetworkPolicy", ["name"]) == set()
