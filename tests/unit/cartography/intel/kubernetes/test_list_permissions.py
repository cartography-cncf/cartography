import gc
import weakref
from types import SimpleNamespace
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from kubernetes.client import V1Namespace
from kubernetes.client import V1ObjectMeta
from kubernetes.client import V1Pod
from kubernetes.client import V1PodSpec
from kubernetes.client import V1PodStatus
from kubernetes.client import V1ReplicaSet
from kubernetes.client import V1Service
from kubernetes.client import V1ServiceAccount
from kubernetes.client import V1ServiceSpec
from kubernetes.client.exceptions import ApiException

from cartography.intel.kubernetes.ingress import sync_ingress
from cartography.intel.kubernetes.namespaces import sync_namespaces
from cartography.intel.kubernetes.networkpolicies import sync_network_policies
from cartography.intel.kubernetes.nodes import sync_nodes
from cartography.intel.kubernetes.pods import sync_pods
from cartography.intel.kubernetes.rbac import sync_kubernetes_rbac
from cartography.intel.kubernetes.secrets import sync_secrets
from cartography.intel.kubernetes.services import sync_services
from cartography.intel.kubernetes.target_group_bindings import (
    sync_target_group_bindings,
)
from cartography.intel.kubernetes.workloads import sync_workloads

COMMON = {"CLUSTER_ID": "cluster-id", "UPDATE_TAG": 1}

SYNCS = [
    pytest.param(
        "cartography.intel.kubernetes.nodes",
        "get_nodes",
        "load_nodes",
        lambda client: sync_nodes(MagicMock(), client, 1, COMMON),
        {},
        id="nodes",
    ),
    pytest.param(
        "cartography.intel.kubernetes.services",
        "get_services",
        "load_services",
        lambda client: sync_services(MagicMock(), client, [], 1, COMMON),
        None,
        id="services",
    ),
    pytest.param(
        "cartography.intel.kubernetes.ingress",
        "get_ingress",
        "load_ingresses",
        lambda client: sync_ingress(MagicMock(), client, 1, COMMON),
        None,
        id="ingress",
    ),
    pytest.param(
        "cartography.intel.kubernetes.target_group_bindings",
        "get_target_group_bindings",
        "load_target_group_bindings",
        lambda client: sync_target_group_bindings(MagicMock(), client, 1, COMMON),
        None,
        id="target_group_bindings",
    ),
]


@pytest.mark.parametrize("module,getter,loader,run,expected", SYNCS)
@pytest.mark.parametrize("status", [401, 403])
def test_forbidden_list_skips_load_and_cleanup(
    module, getter, loader, run, expected, status, caplog
):
    # Arrange
    client = MagicMock(gke_cluster=None)
    client.name = "my-cluster"

    # Act
    with (
        patch(f"{module}.{getter}", side_effect=ApiException(status=status)),
        patch(f"{module}.{loader}") as mock_load,
        patch(f"{module}.cleanup") as mock_cleanup,
        caplog.at_level("WARNING"),
    ):
        result = run(client)

    # Assert
    assert result == expected
    mock_load.assert_not_called()
    mock_cleanup.assert_not_called()
    assert any("lacks permission" in r.message for r in caplog.records)


@pytest.mark.parametrize("module,getter,loader,run,expected", SYNCS)
def test_other_list_errors_raise_without_cleanup(module, getter, loader, run, expected):
    # Arrange
    client = MagicMock(gke_cluster=None)
    client.name = "my-cluster"

    # Act and assert
    with (
        patch(f"{module}.{getter}", side_effect=ApiException(status=500)),
        patch(f"{module}.cleanup") as mock_cleanup,
        pytest.raises(ApiException),
    ):
        run(client)
    mock_cleanup.assert_not_called()


PAGED_SYNCS = [
    pytest.param(
        "cartography.intel.kubernetes.pods",
        "core.list_pod_for_all_namespaces",
        "load_pods",
        lambda client: sync_pods(MagicMock(), client, 1, COMMON),
        id="pods",
    ),
    pytest.param(
        "cartography.intel.kubernetes.namespaces",
        "core.list_namespace",
        "load_namespaces",
        lambda client: sync_namespaces(MagicMock(), client, 1, COMMON),
        id="namespaces",
    ),
    pytest.param(
        "cartography.intel.kubernetes.secrets",
        "core.list_secret_for_all_namespaces",
        "load_secrets",
        lambda client: sync_secrets(MagicMock(), client, 1, COMMON),
        id="secrets",
    ),
    pytest.param(
        "cartography.intel.kubernetes.networkpolicies",
        "networking.list_network_policy_for_all_namespaces",
        "load_network_policies",
        lambda client: sync_network_policies(MagicMock(), client, [], 1, COMMON),
        id="network_policies",
    ),
]


@pytest.mark.parametrize("module,list_path,loader,run", PAGED_SYNCS)
def test_list_error_after_a_page_skips_load_and_cleanup(module, list_path, loader, run):
    # Arrange: the first page succeeds, the second fails.
    client = MagicMock(gke_cluster=None)
    client.name = "my-cluster"
    api_name, list_name = list_path.split(".")
    list_func = getattr(getattr(client, api_name), list_name)
    list_func.__name__ = list_name
    list_func.side_effect = [
        MagicMock(items=[], metadata=MagicMock(_continue="next")),
        ApiException(status=500),
    ]

    # Act and assert
    with (
        patch(f"{module}.{loader}") as mock_load,
        patch(f"{module}.cleanup") as mock_cleanup,
        pytest.raises(ApiException),
    ):
        run(client)
    mock_load.assert_not_called()
    mock_cleanup.assert_not_called()


class _EmptyListApi:
    def __getattr__(self, name):
        def list_func(limit, _continue=None):
            return SimpleNamespace(items=[], metadata=SimpleNamespace(_continue=None))

        list_func.__name__ = name
        return list_func


def _metadata(name: str) -> V1ObjectMeta:
    return V1ObjectMeta(uid=name, name=name, namespace="ns")


STREAMED_SYNCS = [
    pytest.param(
        "cartography.intel.kubernetes.workloads",
        "apps.list_replica_set_for_all_namespaces",
        lambda name: V1ReplicaSet(metadata=_metadata(name)),
        lambda client: sync_workloads(MagicMock(), client, 1, COMMON),
        id="workloads",
    ),
    pytest.param(
        "cartography.intel.kubernetes.rbac",
        "core.list_service_account_for_all_namespaces",
        lambda name: V1ServiceAccount(metadata=_metadata(name)),
        lambda client: sync_kubernetes_rbac(MagicMock(), client, 1, COMMON),
        id="rbac",
    ),
    pytest.param(
        "cartography.intel.kubernetes.services",
        "core.list_service_for_all_namespaces",
        lambda name: V1Service(metadata=_metadata(name), spec=V1ServiceSpec()),
        lambda client: sync_services(MagicMock(), client, [], 1, COMMON),
        id="services",
    ),
    pytest.param(
        "cartography.intel.kubernetes.namespaces",
        "core.list_namespace",
        lambda name: V1Namespace(metadata=_metadata(name)),
        lambda client: sync_namespaces(MagicMock(), client, 1, COMMON),
        id="namespaces",
    ),
    pytest.param(
        "cartography.intel.kubernetes.pods",
        "core.list_pod_for_all_namespaces",
        lambda name: V1Pod(
            metadata=_metadata(name),
            spec=V1PodSpec(containers=[]),
            status=V1PodStatus(),
        ),
        lambda client: sync_pods(MagicMock(), client, 1, COMMON),
        id="pods",
    ),
]


@pytest.mark.parametrize("module,list_path,make_item,run", STREAMED_SYNCS)
def test_sync_holds_at_most_one_page_of_client_models(
    module, list_path, make_item, run
):
    # Arrange: serve five pages of two models, and count on each fetch how many
    # models from earlier pages are still referenced.
    page_size, page_count = 2, 5
    served: list[weakref.ref] = []
    alive_on_fetch: list[int] = []

    def list_func(limit, _continue=None):
        gc.collect()
        alive_on_fetch.append(sum(ref() is not None for ref in served))
        index = int(_continue or 0)
        items = [make_item(f"item-{index}-{n}") for n in range(page_size)]
        served.extend(weakref.ref(item) for item in items)
        next_token = str(index + 1) if index + 1 < page_count else None
        return SimpleNamespace(
            items=items, metadata=SimpleNamespace(_continue=next_token)
        )

    api_name, list_name = list_path.split(".")
    list_func.__name__ = list_name
    client = SimpleNamespace(
        name="my-cluster",
        gke_cluster=None,
        **{api: _EmptyListApi() for api in ("core", "apps", "batch", "rbac")},
    )
    setattr(getattr(client, api_name), list_name, list_func)

    # Act
    with patch(f"{module}.load"), patch(f"{module}.cleanup"):
        run(client)

    # Assert
    assert len(alive_on_fetch) == page_count
    assert max(alive_on_fetch) <= page_size
