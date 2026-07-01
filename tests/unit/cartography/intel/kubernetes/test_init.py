from types import SimpleNamespace

import cartography.intel.kubernetes as kubernetes


def test_start_k8s_ingestion_uses_external_id_for_eks_region(monkeypatch):
    cluster_arn = "arn:aws:eks:us-east-1:111122223333:cluster/example-eks-cluster"
    captured = {}

    class DummyClient:
        name = "dummy-context"

    def _capture_sync_eks(*args, **kwargs):
        # args: session, client, boto3_session, region, update_tag, cluster_id, cluster_name
        captured["region"] = args[3]
        captured["cluster_id"] = args[5]
        captured["cluster_name"] = args[6]

    monkeypatch.setattr(kubernetes, "get_k8s_clients", lambda _: [DummyClient()])
    monkeypatch.setattr(
        kubernetes,
        "sync_kubernetes_cluster",
        lambda *args, **kwargs: {
            "id": "11111111-2222-4333-8444-555555555555",
            "external_id": cluster_arn,
            "name": cluster_arn,
        },
    )
    monkeypatch.setattr(kubernetes, "sync_namespaces", lambda *args, **kwargs: None)
    monkeypatch.setattr(kubernetes, "sync_nodes", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        kubernetes, "sync_kubernetes_rbac", lambda *args, **kwargs: None
    )
    monkeypatch.setattr(kubernetes, "sync_pods", lambda *args, **kwargs: [])
    monkeypatch.setattr(kubernetes, "sync_secrets", lambda *args, **kwargs: None)
    monkeypatch.setattr(kubernetes, "sync_services", lambda *args, **kwargs: None)
    monkeypatch.setattr(kubernetes, "sync_gateway_api", lambda *args, **kwargs: None)
    monkeypatch.setattr(kubernetes, "sync_ingress", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        kubernetes, "run_scoped_analysis_job", lambda *args, **kwargs: None
    )
    monkeypatch.setattr(kubernetes, "sync_eks", _capture_sync_eks)
    monkeypatch.setattr(kubernetes.boto3, "Session", lambda: object())

    config = SimpleNamespace(
        update_tag=123456789,
        k8s_kubeconfig="/tmp/kubeconfig",
        managed_kubernetes="eks",
        k8s_eks_cluster_names=None,
        k8s_eks_region=None,
    )

    kubernetes.start_k8s_ingestion(session=object(), config=config)

    assert captured["region"] == "us-east-1"
    assert captured["cluster_id"] == "11111111-2222-4333-8444-555555555555"
    assert captured["cluster_name"] == cluster_arn


def test_start_k8s_ingestion_eks_region_defaults_to_session(monkeypatch):
    # With --k8s-eks-cluster-names and no --k8s-eks-region, the region comes from
    # the boto3 session's resolved region.
    captured = {}

    class DummySession:
        region_name = "eu-west-1"

    def _fake_session(region_name=None):
        # mimic boto3.Session: explicit region wins, else resolved default
        s = DummySession()
        s.region_name = region_name or "eu-west-1"
        return s

    def _capture_eks_clients(cluster_names, session):
        captured["cluster_names"] = cluster_names
        captured["session_region"] = session.region_name
        return []  # no clients -> sync loop is a no-op

    monkeypatch.setattr(kubernetes.boto3, "Session", _fake_session)
    monkeypatch.setattr(kubernetes, "get_eks_k8s_clients", _capture_eks_clients)

    config = SimpleNamespace(
        update_tag=123456789,
        k8s_kubeconfig=None,
        managed_kubernetes=None,
        k8s_eks_cluster_names="cluster-a, cluster-b",
        k8s_eks_region=None,
    )

    kubernetes.start_k8s_ingestion(session=object(), config=config)

    assert captured["session_region"] == "eu-west-1"
    assert captured["cluster_names"] == ["cluster-a", "cluster-b"]
