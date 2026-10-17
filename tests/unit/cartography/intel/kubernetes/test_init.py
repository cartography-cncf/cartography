from types import SimpleNamespace

import pytest

import cartography.intel.kubernetes as kubernetes

CLUSTER_ARN = "arn:aws:eks:us-east-1:111122223333:cluster/example-eks-cluster"


class DummyClient:
    name = "dummy-context"


def _returning(value):
    return lambda *args, **kwargs: value


def _stub_cluster_sync(monkeypatch):
    monkeypatch.setattr(kubernetes, "get_k8s_clients", lambda _: [DummyClient()])
    monkeypatch.setattr(
        kubernetes,
        "sync_kubernetes_cluster",
        _returning(
            {
                "id": "11111111-2222-4333-8444-555555555555",
                "external_id": CLUSTER_ARN,
                "name": CLUSTER_ARN,
            }
        ),
    )
    monkeypatch.setattr(kubernetes, "sync_namespaces", _returning(None))
    monkeypatch.setattr(kubernetes, "sync_nodes", _returning({}))
    monkeypatch.setattr(kubernetes, "sync_kubernetes_rbac", _returning(None))
    monkeypatch.setattr(kubernetes, "sync_workloads", _returning({}))
    monkeypatch.setattr(kubernetes, "sync_storage", _returning(None))
    monkeypatch.setattr(kubernetes, "sync_pods", _returning([]))
    monkeypatch.setattr(kubernetes, "sync_secrets", _returning(None))
    monkeypatch.setattr(kubernetes, "sync_services", _returning(True))
    monkeypatch.setattr(kubernetes, "sync_network_policies", _returning(None))
    monkeypatch.setattr(kubernetes, "sync_gateway_api", _returning(True))
    monkeypatch.setattr(kubernetes, "sync_ingress", _returning(True))
    monkeypatch.setattr(kubernetes, "sync_eks", _returning(None))
    monkeypatch.setattr(kubernetes, "run_typed_analysis_job", _returning(None))
    monkeypatch.setattr(kubernetes.boto3, "Session", lambda: object())


def _start(managed_kubernetes=None):
    kubernetes.start_k8s_ingestion(
        session=object(),
        config=SimpleNamespace(
            update_tag=123456789,
            k8s_kubeconfig="/tmp/kubeconfig",
            managed_kubernetes=managed_kubernetes,
        ),
    )


def test_start_k8s_ingestion_uses_external_id_for_eks_region(monkeypatch):
    # Arrange
    captured = {}

    def _capture_sync_eks(*args, **kwargs):
        # args: session, client, boto3_session, region, update_tag, cluster_id, cluster_name
        captured["region"] = args[3]
        captured["cluster_id"] = args[5]
        captured["cluster_name"] = args[6]

    _stub_cluster_sync(monkeypatch)
    monkeypatch.setattr(kubernetes, "sync_eks", _capture_sync_eks)

    # Act
    _start(managed_kubernetes="eks")

    # Assert
    assert captured["region"] == "us-east-1"
    assert captured["cluster_id"] == "11111111-2222-4333-8444-555555555555"
    assert captured["cluster_name"] == CLUSTER_ARN


@pytest.mark.parametrize(
    "sync_name,result,check_inputs_synced",
    [
        ("sync_services", True, True),
        ("sync_nodes", None, False),
        ("sync_services", False, False),
        ("sync_gateway_api", False, False),
        ("sync_ingress", False, False),
    ],
    ids=[
        "every_list_succeeded",
        "node_list_failed",
        "service_list_failed",
        "gateway_api_list_denied",
        "ingress_list_failed",
    ],
)
def test_cluster_check_vouches_only_for_lists_that_succeeded(
    monkeypatch, sync_name, result, check_inputs_synced
):
    # Arrange
    params_by_job = {}

    def _run_job(job, session, params):
        params_by_job[job.short_name] = params

    _stub_cluster_sync(monkeypatch)
    monkeypatch.setattr(kubernetes, sync_name, _returning(result))
    monkeypatch.setattr(kubernetes, "run_typed_analysis_job", _run_job)

    # Act
    _start()

    # Assert
    cluster_check = params_by_job["k8s_unmodeled_internet_paths"]
    assert cluster_check["CHECK_INPUTS_SYNCED"] is check_inputs_synced
