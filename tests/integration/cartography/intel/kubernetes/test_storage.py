from types import SimpleNamespace

import pytest
from kubernetes.client.exceptions import ApiException

import cartography.intel.kubernetes.pods as pods_module
import cartography.intel.kubernetes.storage as storage_module
from cartography.intel.kubernetes.clusters import load_kubernetes_cluster
from cartography.intel.kubernetes.namespaces import load_namespaces
from cartography.intel.kubernetes.pods import sync_pods
from cartography.intel.kubernetes.storage import sync_storage
from tests.data.kubernetes.clusters import KUBERNETES_CLUSTER_DATA
from tests.data.kubernetes.clusters import KUBERNETES_CLUSTER_IDS
from tests.data.kubernetes.clusters import KUBERNETES_CLUSTER_NAMES
from tests.data.kubernetes.namespaces import KUBERNETES_CLUSTER_1_NAMESPACES_DATA
from tests.data.kubernetes.storage import CLAIM_NAME
from tests.data.kubernetes.storage import NAMESPACE
from tests.data.kubernetes.storage import RAW_GPU_PODS
from tests.data.kubernetes.storage import RAW_PERSISTENT_VOLUME_CLAIMS
from tests.data.kubernetes.storage import RAW_PERSISTENT_VOLUMES
from tests.data.kubernetes.storage import RAW_STORAGE_CLASSES
from tests.data.kubernetes.storage import STORAGE_CLASS_NAME
from tests.data.kubernetes.storage import VOLUME_NAME
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
CLUSTER_ID = KUBERNETES_CLUSTER_IDS[0]
CLUSTER_NAME = KUBERNETES_CLUSTER_NAMES[0]


@pytest.fixture
def _create_test_cluster(neo4j_session):
    # Arrange
    load_kubernetes_cluster(neo4j_session, KUBERNETES_CLUSTER_DATA, TEST_UPDATE_TAG)
    load_namespaces(
        neo4j_session,
        KUBERNETES_CLUSTER_1_NAMESPACES_DATA,
        TEST_UPDATE_TAG,
        CLUSTER_NAME,
        CLUSTER_ID,
    )


def _mock_storage(monkeypatch):
    monkeypatch.setattr(
        storage_module,
        "get_storage_classes",
        lambda client: RAW_STORAGE_CLASSES,
    )
    monkeypatch.setattr(
        storage_module,
        "get_persistent_volumes",
        lambda client: RAW_PERSISTENT_VOLUMES,
    )
    monkeypatch.setattr(
        storage_module,
        "get_persistent_volume_claims",
        lambda client: RAW_PERSISTENT_VOLUME_CLAIMS,
    )


def test_sync_storage(neo4j_session, monkeypatch, _create_test_cluster):
    # Arrange
    _mock_storage(monkeypatch)
    client = SimpleNamespace(name=CLUSTER_NAME)
    common_job_parameters = {"UPDATE_TAG": TEST_UPDATE_TAG, "CLUSTER_ID": CLUSTER_ID}

    # Act
    sync_storage(neo4j_session, client, TEST_UPDATE_TAG, common_job_parameters)

    # Assert
    assert check_nodes(
        neo4j_session,
        "KubernetesPersistentVolume",
        ["name", "capacity_storage", "csi_driver", "phase"],
    ) == {(VOLUME_NAME, "2Pi", "csi.example.com", "Bound")}
    assert check_nodes(
        neo4j_session,
        "KubernetesPersistentVolumeClaim",
        ["name", "requested_storage", "phase"],
    ) == {(CLAIM_NAME, "2Pi", "Bound")}
    assert check_rels(
        neo4j_session,
        "KubernetesPersistentVolumeClaim",
        "name",
        "KubernetesPersistentVolume",
        "name",
        "BOUND_TO",
    ) == {(CLAIM_NAME, VOLUME_NAME)}
    assert check_rels(
        neo4j_session,
        "KubernetesPersistentVolumeClaim",
        "name",
        "KubernetesStorageClass",
        "name",
        "USES_STORAGE_CLASS",
    ) == {(CLAIM_NAME, STORAGE_CLASS_NAME)}
    assert check_rels(
        neo4j_session,
        "KubernetesPersistentVolume",
        "name",
        "KubernetesStorageClass",
        "name",
        "USES_STORAGE_CLASS",
    ) == {(VOLUME_NAME, STORAGE_CLASS_NAME)}
    assert check_rels(
        neo4j_session,
        "KubernetesNamespace",
        "name",
        "KubernetesPersistentVolumeClaim",
        "name",
        "CONTAINS",
    ) == {(NAMESPACE, CLAIM_NAME)}


def test_pod_mounts_persistent_volume_claim(
    neo4j_session,
    monkeypatch,
    _create_test_cluster,
):
    # Arrange
    _mock_storage(monkeypatch)
    monkeypatch.setattr(pods_module, "get_pods", lambda client: RAW_GPU_PODS)
    client = SimpleNamespace(name=CLUSTER_NAME)
    common_job_parameters = {"UPDATE_TAG": TEST_UPDATE_TAG, "CLUSTER_ID": CLUSTER_ID}
    sync_storage(neo4j_session, client, TEST_UPDATE_TAG, common_job_parameters)

    # Act
    sync_pods(neo4j_session, client, TEST_UPDATE_TAG, common_job_parameters)

    # Assert
    assert check_rels(
        neo4j_session,
        "KubernetesPod",
        "name",
        "KubernetesPersistentVolumeClaim",
        "name",
        "MOUNTS",
    ) == {("training-job-head", CLAIM_NAME)}
    assert check_nodes(
        neo4j_session,
        "KubernetesContainer",
        ["name", "gpu_request", "gpu_limit", "resource_requests"],
    ) == {
        (
            "worker",
            8,
            8,
            '{"cpu": "32", "memory": "600Gi", "nvidia.com/gpu": "8"}',
        )
    }


def test_sync_storage_preserves_nodes_when_forbidden(
    neo4j_session,
    monkeypatch,
    _create_test_cluster,
):
    # Arrange
    _mock_storage(monkeypatch)
    client = SimpleNamespace(name=CLUSTER_NAME)
    common_job_parameters = {"UPDATE_TAG": TEST_UPDATE_TAG, "CLUSTER_ID": CLUSTER_ID}
    sync_storage(neo4j_session, client, TEST_UPDATE_TAG, common_job_parameters)
    monkeypatch.setattr(
        storage_module,
        "get_storage_classes",
        lambda client: (_ for _ in ()).throw(ApiException(status=403)),
    )

    # Act
    sync_storage(
        neo4j_session,
        client,
        TEST_UPDATE_TAG + 1,
        {"UPDATE_TAG": TEST_UPDATE_TAG + 1, "CLUSTER_ID": CLUSTER_ID},
    )

    # Assert
    assert check_nodes(neo4j_session, "KubernetesStorageClass", ["name"]) == {
        (STORAGE_CLASS_NAME,)
    }


def test_sync_storage_cleans_up_stale_nodes(
    neo4j_session,
    monkeypatch,
    _create_test_cluster,
):
    # Arrange
    _mock_storage(monkeypatch)
    client = SimpleNamespace(name=CLUSTER_NAME)
    common_job_parameters = {"UPDATE_TAG": TEST_UPDATE_TAG, "CLUSTER_ID": CLUSTER_ID}
    sync_storage(neo4j_session, client, TEST_UPDATE_TAG, common_job_parameters)
    monkeypatch.setattr(storage_module, "get_storage_classes", lambda client: [])
    monkeypatch.setattr(storage_module, "get_persistent_volumes", lambda client: [])
    monkeypatch.setattr(
        storage_module,
        "get_persistent_volume_claims",
        lambda client: [],
    )

    # Act
    sync_storage(
        neo4j_session,
        client,
        TEST_UPDATE_TAG + 1,
        {"UPDATE_TAG": TEST_UPDATE_TAG + 1, "CLUSTER_ID": CLUSTER_ID},
    )

    # Assert
    assert check_nodes(neo4j_session, "KubernetesStorageClass", ["name"]) == set()
    assert check_nodes(neo4j_session, "KubernetesPersistentVolume", ["name"]) == set()
    assert (
        check_nodes(
            neo4j_session,
            "KubernetesPersistentVolumeClaim",
            ["name"],
        )
        == set()
    )
