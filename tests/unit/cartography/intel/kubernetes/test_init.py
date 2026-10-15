from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from kubernetes.client.exceptions import ApiException

import cartography.intel.kubernetes as kubernetes
from cartography.analysis.kubernetes.analysis import K8S_UNMODELED_INTERNET_PATHS
from cartography.intel.kubernetes import gateway_api
from cartography.intel.kubernetes import ingress
from cartography.intel.kubernetes import nodes
from cartography.intel.kubernetes import services

CLUSTER_ARN = "arn:aws:eks:us-east-1:111122223333:cluster/example-eks-cluster"


def _stub_cluster_sync(monkeypatch, **syncs):
    class DummyClient:
        name = "dummy-context"

    monkeypatch.setattr(kubernetes, "get_k8s_clients", lambda _: [DummyClient()])
    monkeypatch.setattr(
        kubernetes,
        "sync_kubernetes_cluster",
        lambda *args, **kwargs: {
            "id": "11111111-2222-4333-8444-555555555555",
            "external_id": CLUSTER_ARN,
            "name": CLUSTER_ARN,
        },
    )
    results = {
        "sync_namespaces": None,
        "sync_nodes": {},
        "sync_kubernetes_rbac": None,
        "sync_workloads": {},
        "sync_storage": None,
        "sync_pods": [],
        "sync_secrets": None,
        "sync_services": True,
        "sync_network_policies": None,
        "sync_gateway_api": True,
        "sync_ingress": True,
        "sync_eks": None,
    }
    for name, result in results.items():
        monkeypatch.setattr(
            kubernetes, name, lambda *args, result=result, **kwargs: result
        )
    for name, sync in syncs.items():
        monkeypatch.setattr(kubernetes, name, sync)
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
    captured = {}

    def _capture_sync_eks(*args, **kwargs):
        # args: session, client, boto3_session, region, update_tag, cluster_id, cluster_name
        captured["region"] = args[3]
        captured["cluster_id"] = args[5]
        captured["cluster_name"] = args[6]

    _stub_cluster_sync(
        monkeypatch,
        sync_eks=_capture_sync_eks,
        run_typed_analysis_job=lambda *args, **kwargs: None,
    )

    _start(managed_kubernetes="eks")

    assert captured["region"] == "us-east-1"
    assert captured["cluster_id"] == "11111111-2222-4333-8444-555555555555"
    assert captured["cluster_name"] == CLUSTER_ARN


@pytest.mark.parametrize(
    "failed_sync,expected",
    [
        ({}, True),
        ({"sync_nodes": None}, False),
        ({"sync_services": False}, False),
        ({"sync_gateway_api": False}, False),
        ({"sync_ingress": False}, False),
    ],
    ids=["complete", "nodes", "services", "gateway_api", "ingress"],
)
def test_cluster_check_needs_every_list_to_succeed(monkeypatch, failed_sync, expected):
    checks = []

    def _run_job(job, session, params):
        if job is K8S_UNMODELED_INTERNET_PATHS:
            checks.append(params["CHECK_INPUTS_SYNCED"])

    _stub_cluster_sync(
        monkeypatch,
        run_typed_analysis_job=_run_job,
        **{
            name: lambda *args, result=result, **kwargs: result
            for name, result in failed_sync.items()
        },
    )

    _start()

    assert checks == [expected]


def _paged_list(fails):
    def list_for_all_namespaces(limit, _continue=None):
        if _continue:
            # The continue token expired after the first page.
            raise ApiException(status=410, reason="Gone")
        return SimpleNamespace(
            items=[], metadata=SimpleNamespace(_continue="next" if fails else None)
        )

    return list_for_all_namespaces


def _custom_objects(fails):
    def list_cluster_custom_object(**kwargs):
        if fails:
            raise ApiException(status=403, reason="Forbidden")
        return {"items": []}

    return list_cluster_custom_object


PARAMS = {"UPDATE_TAG": 1, "CLUSTER_ID": "cluster"}


@pytest.mark.parametrize(
    "module,api,list_name,make_list,sync,failed,synced",
    [
        (
            services,
            "core",
            "list_service_for_all_namespaces",
            _paged_list,
            lambda client: services.sync_services(None, client, [], 1, PARAMS),
            False,
            True,
        ),
        (
            ingress,
            "networking",
            "list_ingress_for_all_namespaces",
            _paged_list,
            lambda client: ingress.sync_ingress(None, client, 1, PARAMS),
            False,
            True,
        ),
        (
            nodes,
            "core",
            "list_node",
            _paged_list,
            lambda client: nodes.sync_nodes(None, client, 1, PARAMS),
            None,
            {},
        ),
        (
            gateway_api,
            "custom",
            "list_cluster_custom_object",
            _custom_objects,
            lambda client: gateway_api.sync_gateway_api(None, client, 1, PARAMS),
            False,
            True,
        ),
    ],
    ids=["services", "ingress", "nodes", "gateway_api"],
)
@pytest.mark.parametrize("fails", [False, True], ids=["listed", "list_failed"])
def test_failed_list_keeps_the_previous_nodes_and_is_reported(
    monkeypatch, module, api, list_name, make_list, sync, failed, synced, fails
):
    cleanup = MagicMock()
    monkeypatch.setattr(module, "cleanup", cleanup)
    client = SimpleNamespace(
        name="example", **{api: SimpleNamespace(**{list_name: make_list(fails)})}
    )

    result = sync(client)

    assert result == (failed if fails else synced)
    # A partial list must not let cleanup delete what it did not return.
    assert cleanup.called is not fails
