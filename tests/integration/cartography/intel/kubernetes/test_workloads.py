from types import SimpleNamespace

import pytest
from kubernetes.client.exceptions import ApiException

import cartography.intel.kubernetes.pods as pods
import cartography.intel.kubernetes.workloads as workloads
from cartography.intel.kubernetes.clusters import load_kubernetes_cluster
from cartography.intel.kubernetes.namespaces import load_namespaces
from cartography.intel.kubernetes.pods import sync_pods
from cartography.intel.kubernetes.workloads import sync_workloads
from tests.data.kubernetes import workloads as workload_data
from tests.data.kubernetes.clusters import KUBERNETES_CLUSTER_DATA
from tests.data.kubernetes.clusters import KUBERNETES_CLUSTER_IDS
from tests.data.kubernetes.clusters import KUBERNETES_CLUSTER_NAMES
from tests.data.kubernetes.namespaces import KUBERNETES_CLUSTER_1_NAMESPACES_DATA
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789


@pytest.fixture
def _create_test_cluster(neo4j_session):
    load_kubernetes_cluster(neo4j_session, KUBERNETES_CLUSTER_DATA, TEST_UPDATE_TAG)
    load_namespaces(
        neo4j_session,
        KUBERNETES_CLUSTER_1_NAMESPACES_DATA,
        TEST_UPDATE_TAG,
        KUBERNETES_CLUSTER_NAMES[0],
        KUBERNETES_CLUSTER_IDS[0],
    )
    yield
    # Clear every Kubernetes node so workload/pod state does not leak between
    # tests (the forbidden-sync tests assert on the absence of controller nodes).
    for label in (
        "KubernetesContainer",
        "KubernetesPod",
        "KubernetesDeployment",
        "KubernetesReplicaSet",
        "KubernetesStatefulSet",
        "KubernetesDaemonSet",
        "KubernetesJob",
        "KubernetesCronJob",
        "KubernetesNamespace",
        "KubernetesCluster",
    ):
        neo4j_session.run(f"MATCH (n:{label}) DETACH DELETE n")


def _run_sync(neo4j_session, monkeypatch):
    client = SimpleNamespace(name=KUBERNETES_CLUSTER_NAMES[0])
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "CLUSTER_ID": KUBERNETES_CLUSTER_IDS[0],
    }

    monkeypatch.setattr(
        workloads, "get_deployments", lambda c: workload_data.get_raw_deployments()
    )
    monkeypatch.setattr(
        workloads, "get_replicasets", lambda c: workload_data.get_raw_replicasets()
    )
    monkeypatch.setattr(
        workloads, "get_statefulsets", lambda c: workload_data.get_raw_statefulsets()
    )
    monkeypatch.setattr(
        workloads, "get_daemonsets", lambda c: workload_data.get_raw_daemonsets()
    )
    monkeypatch.setattr(
        workloads, "get_cronjobs", lambda c: workload_data.get_raw_cronjobs()
    )
    monkeypatch.setattr(workloads, "get_jobs", lambda c: workload_data.get_raw_jobs())
    monkeypatch.setattr(pods, "get_pods", lambda c: workload_data.get_raw_pods())

    replicaset_owner_map = sync_workloads(
        neo4j_session, client, TEST_UPDATE_TAG, common_job_parameters
    )
    sync_pods(
        neo4j_session,
        client,
        TEST_UPDATE_TAG,
        common_job_parameters,
        replicaset_owner_map=replicaset_owner_map,
    )


def test_workload_nodes(neo4j_session, _create_test_cluster, monkeypatch):
    _run_sync(neo4j_session, monkeypatch)

    assert check_nodes(neo4j_session, "KubernetesDeployment", ["name"]) == {("web",)}
    assert check_nodes(neo4j_session, "KubernetesReplicaSet", ["name"]) == {("web-rs",)}
    assert check_nodes(neo4j_session, "KubernetesStatefulSet", ["name"]) == {("db",)}
    assert check_nodes(neo4j_session, "KubernetesDaemonSet", ["name"]) == {("agent",)}
    assert check_nodes(neo4j_session, "KubernetesCronJob", ["name"]) == {("report",)}
    assert check_nodes(neo4j_session, "KubernetesJob", ["name"]) == {
        ("report-123",),
        ("migrate",),
    }

    # Surfaced controllers carry the ComputeService ontology label; ReplicaSet
    # does not (it is collapsed out of the chain).
    assert check_nodes(neo4j_session, "ComputeService", ["name"]) >= {
        ("web",),
        ("db",),
        ("agent",),
        ("report",),
        ("report-123",),
        ("migrate",),
    }
    assert ("web-rs",) not in check_nodes(neo4j_session, "ComputeService", ["name"])


def test_ownerreferences_edges(neo4j_session, _create_test_cluster, monkeypatch):
    _run_sync(neo4j_session, monkeypatch)

    # Raw ownerReference chain through the (collapsed) ReplicaSet.
    assert check_rels(
        neo4j_session,
        "KubernetesPod",
        "name",
        "KubernetesReplicaSet",
        "name",
        "OWNED_BY",
    ) == {("web-pod", "web-rs")}
    assert check_rels(
        neo4j_session,
        "KubernetesReplicaSet",
        "name",
        "KubernetesDeployment",
        "name",
        "OWNED_BY",
    ) == {("web-rs", "web")}


def test_pod_workload_parent_collapses_replicaset(
    neo4j_session, _create_test_cluster, monkeypatch
):
    _run_sync(neo4j_session, monkeypatch)

    # Pod skips the ReplicaSet and points straight at the Deployment.
    assert check_rels(
        neo4j_session,
        "KubernetesPod",
        "name",
        "KubernetesDeployment",
        "name",
        "WORKLOAD_PARENT",
    ) == {("web-pod", "web")}
    assert check_rels(
        neo4j_session,
        "KubernetesPod",
        "name",
        "KubernetesStatefulSet",
        "name",
        "WORKLOAD_PARENT",
    ) == {("db-pod", "db")}
    assert check_rels(
        neo4j_session,
        "KubernetesPod",
        "name",
        "KubernetesDaemonSet",
        "name",
        "WORKLOAD_PARENT",
    ) == {("agent-pod", "agent")}
    assert check_rels(
        neo4j_session,
        "KubernetesPod",
        "name",
        "KubernetesJob",
        "name",
        "WORKLOAD_PARENT",
    ) == {("report-pod", "report-123"), ("migrate-pod", "migrate")}


def test_controller_workload_parent_up_the_chain(
    neo4j_session, _create_test_cluster, monkeypatch
):
    _run_sync(neo4j_session, monkeypatch)

    # Job owned by a CronJob points at it; standalone Job falls back to namespace.
    assert check_rels(
        neo4j_session,
        "KubernetesJob",
        "name",
        "KubernetesCronJob",
        "name",
        "WORKLOAD_PARENT",
    ) == {("report-123", "report")}

    controller_to_namespace = check_rels(
        neo4j_session,
        "KubernetesNamespace",
        "name",
        "KubernetesJob",
        "name",
        "WORKLOAD_PARENT",
        rel_direction_right=False,
    )
    assert controller_to_namespace == {(workload_data.NAMESPACE, "migrate")}

    # The long-running controllers and the CronJob anchor to the namespace.
    for label in (
        "KubernetesDeployment",
        "KubernetesStatefulSet",
        "KubernetesDaemonSet",
        "KubernetesCronJob",
    ):
        rels = check_rels(
            neo4j_session,
            "KubernetesNamespace",
            "name",
            label,
            "name",
            "WORKLOAD_PARENT",
            rel_direction_right=False,
        )
        assert rels, f"expected {label} -> namespace WORKLOAD_PARENT edge"


def test_forbidden_workload_list_preserves_nodes(
    neo4j_session, _create_test_cluster, monkeypatch
):
    # First a normal sync populates the controllers.
    _run_sync(neo4j_session, monkeypatch)
    assert check_nodes(neo4j_session, "KubernetesDeployment", ["name"]) == {("web",)}

    # A later run where the operator revoked `list deployments` (403) must NOT
    # wipe the existing workload nodes: sync_workloads skips load + cleanup and
    # returns None (signalling "workloads unavailable", distinct from {}).
    client = SimpleNamespace(name=KUBERNETES_CLUSTER_NAMES[0])

    def _forbidden(_c):
        raise ApiException(status=403, reason="Forbidden")

    monkeypatch.setattr(workloads, "get_deployments", _forbidden)

    result = workloads.sync_workloads(
        neo4j_session,
        client,
        TEST_UPDATE_TAG + 1,
        {"UPDATE_TAG": TEST_UPDATE_TAG + 1, "CLUSTER_ID": KUBERNETES_CLUSTER_IDS[0]},
    )

    assert result is None
    # Nodes from the previous successful sync are preserved.
    assert check_nodes(neo4j_session, "KubernetesDeployment", ["name"]) == {("web",)}
    assert check_nodes(neo4j_session, "KubernetesReplicaSet", ["name"]) == {("web-rs",)}


def test_transient_workload_error_skips_and_preserves(
    neo4j_session, _create_test_cluster, monkeypatch
):
    # A non-permission API error (e.g. 500) on any controller list must not be
    # mistaken for a successful empty sync: get_* re-raise (raise_on_error) and
    # sync_workloads returns None, skipping load + cleanup so existing nodes are
    # preserved and pods fall back to a namespace WORKLOAD_PARENT.
    _run_sync(neo4j_session, monkeypatch)
    assert check_nodes(neo4j_session, "KubernetesStatefulSet", ["name"]) == {("db",)}

    client = SimpleNamespace(name=KUBERNETES_CLUSTER_NAMES[0])

    def _server_error(_c):
        raise ApiException(status=500, reason="ServerError")

    monkeypatch.setattr(workloads, "get_statefulsets", _server_error)

    result = workloads.sync_workloads(
        neo4j_session,
        client,
        TEST_UPDATE_TAG + 1,
        {"UPDATE_TAG": TEST_UPDATE_TAG + 1, "CLUSTER_ID": KUBERNETES_CLUSTER_IDS[0]},
    )

    assert result is None
    # Nodes from the previous successful sync are preserved (no destructive cleanup).
    assert check_nodes(neo4j_session, "KubernetesDeployment", ["name"]) == {("web",)}
    assert check_nodes(neo4j_session, "KubernetesStatefulSet", ["name"]) == {("db",)}


def test_forbidden_workloads_pods_fall_back_to_namespace(
    neo4j_session, _create_test_cluster, monkeypatch
):
    # When the workload sync is skipped (403), no controller node is ingested, so
    # every controller-owned pod (StatefulSet/DaemonSet/Job as well as the
    # collapsed ReplicaSet case) must fall back to a namespace WORKLOAD_PARENT
    # rather than being orphaned from the chain.
    client = SimpleNamespace(name=KUBERNETES_CLUSTER_NAMES[0])
    common = {"UPDATE_TAG": TEST_UPDATE_TAG, "CLUSTER_ID": KUBERNETES_CLUSTER_IDS[0]}

    def _forbidden(_c):
        raise ApiException(status=403, reason="Forbidden")

    monkeypatch.setattr(workloads, "get_deployments", _forbidden)
    monkeypatch.setattr(pods, "get_pods", lambda c: workload_data.get_raw_pods())

    rs_map = workloads.sync_workloads(neo4j_session, client, TEST_UPDATE_TAG, common)
    assert rs_map is None
    sync_pods(
        neo4j_session, client, TEST_UPDATE_TAG, common, replicaset_owner_map=rs_map
    )

    # No controller nodes were ingested.
    for label in (
        "KubernetesDeployment",
        "KubernetesStatefulSet",
        "KubernetesDaemonSet",
        "KubernetesJob",
        "KubernetesCronJob",
    ):
        assert check_nodes(neo4j_session, label, ["name"]) == set()

    ns = workload_data.NAMESPACE
    # Every pod (RS/StatefulSet/DaemonSet/Job-owned and the bare pod) falls back
    # to the namespace.
    assert check_rels(
        neo4j_session,
        "KubernetesPod",
        "name",
        "KubernetesNamespace",
        "name",
        "WORKLOAD_PARENT",
    ) == {
        ("web-pod", ns),
        ("db-pod", ns),
        ("agent-pod", ns),
        ("report-pod", ns),
        ("migrate-pod", ns),
        ("bare-pod", ns),
    }


def test_bare_pod_still_resolves_to_namespace(
    neo4j_session, _create_test_cluster, monkeypatch
):
    _run_sync(neo4j_session, monkeypatch)

    # A pod with no controller keeps its namespace WORKLOAD_PARENT (no regression);
    # controlled pods do NOT get a namespace WORKLOAD_PARENT edge.
    pod_to_namespace = check_rels(
        neo4j_session,
        "KubernetesPod",
        "name",
        "KubernetesNamespace",
        "name",
        "WORKLOAD_PARENT",
    )
    assert pod_to_namespace == {("bare-pod", workload_data.NAMESPACE)}
