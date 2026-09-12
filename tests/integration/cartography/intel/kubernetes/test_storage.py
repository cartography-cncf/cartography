import json
from copy import deepcopy
from types import SimpleNamespace

import pytest
from kubernetes.client import V1VolumeDevice
from kubernetes.client.exceptions import ApiException
from urllib3.exceptions import MaxRetryError

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
from tests.data.kubernetes.storage import CREATION_TIMESTAMP
from tests.data.kubernetes.storage import DELETION_TIMESTAMP
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


@pytest.fixture
def _cleanup_block_storage_nodes(neo4j_session):
    yield
    neo4j_session.run(
        """
        MATCH (node)
        WHERE node.cluster_name = $cluster_name
          AND ((node:KubernetesPersistentVolume AND node.name = 'pvc-block-volume')
            OR (node:KubernetesPersistentVolumeClaim AND node.name = 'block-data')
            OR (node:KubernetesPod AND node.name = 'block-training-job')
            OR (node:KubernetesContainer AND node.name = 'block-worker'))
        DETACH DELETE node
        """,
        cluster_name=CLUSTER_NAME,
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
        [
            "name",
            "capacity_storage",
            "capacity_storage_bytes",
            "csi_driver",
            "phase",
        ],
    ) == {(VOLUME_NAME, "2Pi", 2251799813685248, "csi.example.com", "Bound")}
    assert check_nodes(
        neo4j_session,
        "KubernetesPersistentVolumeClaim",
        ["name", "requested_storage", "requested_storage_bytes", "phase"],
    ) == {(CLAIM_NAME, "2Pi", 2251799813685248, "Bound")}
    assert check_nodes(
        neo4j_session,
        "KubernetesStorageClass",
        ["name", "uid"],
    ) == {(STORAGE_CLASS_NAME, "00000000-0000-0000-0000-000000000000")}
    for label, name in (
        ("KubernetesStorageClass", STORAGE_CLASS_NAME),
        ("KubernetesPersistentVolume", VOLUME_NAME),
        ("KubernetesPersistentVolumeClaim", CLAIM_NAME),
    ):
        assert check_nodes(
            neo4j_session,
            label,
            ["name", "creation_timestamp", "deletion_timestamp"],
        ) == {(name, CREATION_TIMESTAMP, DELETION_TIMESTAMP)}
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


def test_transform_persistent_volume_claim_without_requests():
    claim = deepcopy(RAW_PERSISTENT_VOLUME_CLAIMS[0])
    claim.spec.resources.requests = None

    result = storage_module.transform_persistent_volume_claims([claim], CLUSTER_NAME)

    assert result[0]["requested_storage"] is None


def test_transform_persistent_volume_claim_rounds_fractional_bytes_up():
    claim = deepcopy(RAW_PERSISTENT_VOLUME_CLAIMS[0])
    claim.spec.resources.requests = {"storage": "400m"}

    result = storage_module.transform_persistent_volume_claims([claim], CLUSTER_NAME)

    assert result[0]["requested_storage_bytes"] == 1


def test_persistent_volumes_link_to_backing_cloud_disks(
    neo4j_session,
    monkeypatch,
    _create_test_cluster,
):
    # Arrange
    aws_volume = deepcopy(RAW_PERSISTENT_VOLUMES[0])
    aws_volume.metadata.name = "aws-volume"
    aws_volume.metadata.uid = "aws-volume-uid"
    aws_volume.spec.csi.driver = "ebs.csi.aws.com"
    aws_volume.spec.csi.volume_handle = "vol-0123456789abcdef0"

    azure_volume = deepcopy(RAW_PERSISTENT_VOLUMES[0])
    azure_volume.metadata.name = "azure-volume"
    azure_volume.metadata.uid = "azure-volume-uid"
    azure_volume.spec.csi.driver = "disk.csi.azure.com"
    azure_disk_id = (
        "/subscriptions/00000000-0000-0000-0000-000000000000/"
        "resourceGroups/example/providers/Microsoft.Compute/disks/data"
    )
    azure_volume.spec.csi.volume_handle = (
        "/subscriptions/00000000-0000-0000-0000-000000000000/"
        "resourcegroups/example/providers/microsoft.compute/disks/data"
    )

    monkeypatch.setattr(
        storage_module,
        "get_storage_classes",
        lambda client: RAW_STORAGE_CLASSES,
    )
    monkeypatch.setattr(
        storage_module,
        "get_persistent_volumes",
        lambda client: [aws_volume, azure_volume],
    )
    monkeypatch.setattr(
        storage_module,
        "get_persistent_volume_claims",
        lambda client: [],
    )
    neo4j_session.run("MERGE (:AWSEBSVolume {id: 'vol-0123456789abcdef0'})")
    neo4j_session.run(
        "MERGE (:AzureDisk {id: $id})",
        id=azure_disk_id,
    )
    client = SimpleNamespace(name=CLUSTER_NAME)

    # Act
    sync_storage(
        neo4j_session,
        client,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "CLUSTER_ID": CLUSTER_ID},
    )

    # Assert
    assert check_rels(
        neo4j_session,
        "KubernetesPersistentVolume",
        "name",
        "AWSEBSVolume",
        "id",
        "BACKED_BY",
    ) == {("aws-volume", "vol-0123456789abcdef0")}
    assert check_rels(
        neo4j_session,
        "KubernetesPersistentVolume",
        "name",
        "AzureDisk",
        "id",
        "BACKED_BY",
    ) == {("azure-volume", azure_disk_id)}
    neo4j_session.run(
        "MATCH (v) "
        "WHERE (v:KubernetesPersistentVolume AND "
        "v.name IN ['aws-volume', 'azure-volume']) "
        "OR (v:AWSEBSVolume AND v.id = 'vol-0123456789abcdef0') "
        "OR (v:AzureDisk AND v.id = $azure_disk_id) "
        "DETACH DELETE v",
        azure_disk_id=azure_disk_id,
    )
    assert check_nodes(neo4j_session, "AWSEBSVolume", ["id"]) == set()
    assert check_nodes(neo4j_session, "AzureDisk", ["id"]) == set()


def test_pod_references_and_container_mounts_persistent_volume_claim(
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
        "REFERENCES",
    ) == {("training-job-head", CLAIM_NAME)}
    assert check_rels(
        neo4j_session,
        "KubernetesContainer",
        "name",
        "KubernetesPersistentVolumeClaim",
        "name",
        "MOUNTS",
    ) == {("worker", CLAIM_NAME)}
    container = neo4j_session.run(
        """
        MATCH (container:KubernetesContainer {name: $container_name})
              -[:MOUNTS]->
              (:KubernetesPersistentVolumeClaim {name: $claim_name})
        RETURN container.persistent_volume_claim_ids AS internal_claim_ids,
               container.persistent_volume_claim_read_write_ids AS read_write_claim_ids,
               container.persistent_volume_claim_mounts AS mount_details
        """,
        container_name="worker",
        claim_name=CLAIM_NAME,
    ).single()
    assert container is not None
    assert container["internal_claim_ids"] is None
    assert container["read_write_claim_ids"] == [
        f"{CLUSTER_NAME}/my-namespace/{CLAIM_NAME}"
    ]
    assert json.loads(container["mount_details"]) == [
        {
            "claim_id": f"{CLUSTER_NAME}/my-namespace/{CLAIM_NAME}",
            "claim_name": CLAIM_NAME,
            "volume_name": "shared-data",
            "mount_path": "/data",
            "mount_propagation": "None",
            "read_only": False,
            "recursive_read_only": None,
            "sub_path": "checkpoints",
            "sub_path_expr": None,
        }
    ]
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


def test_container_uses_persistent_volume_claim_as_raw_block_device(
    neo4j_session,
    monkeypatch,
    _create_test_cluster,
    _cleanup_block_storage_nodes,
):
    # Arrange
    block_volume = deepcopy(RAW_PERSISTENT_VOLUMES[0])
    block_volume.metadata.name = "pvc-block-volume"
    block_volume.metadata.uid = "00000000-0000-0000-0000-000000000005"
    block_volume.spec.volume_mode = "Block"
    block_volume.spec.claim_ref.name = "block-data"
    block_claim = deepcopy(RAW_PERSISTENT_VOLUME_CLAIMS[0])
    block_claim.metadata.name = "block-data"
    block_claim.metadata.uid = "00000000-0000-0000-0000-000000000006"
    block_claim.spec.volume_mode = "Block"
    block_claim.spec.volume_name = block_volume.metadata.name
    block_pod = deepcopy(RAW_GPU_PODS[0])
    block_pod.metadata.name = "block-training-job"
    block_pod.metadata.uid = "00000000-0000-0000-0000-000000000007"
    block_pod.spec.volumes[0].persistent_volume_claim.claim_name = "block-data"
    block_pod.spec.containers[0].name = "block-worker"
    block_pod.spec.containers[0].volume_mounts = []
    block_pod.spec.containers[0].volume_devices = [
        V1VolumeDevice(name="shared-data", device_path="/dev/training-data")
    ]
    monkeypatch.setattr(
        storage_module,
        "get_storage_classes",
        lambda client: RAW_STORAGE_CLASSES,
    )
    monkeypatch.setattr(
        storage_module,
        "get_persistent_volumes",
        lambda client: [block_volume],
    )
    monkeypatch.setattr(
        storage_module,
        "get_persistent_volume_claims",
        lambda client: [block_claim],
    )
    monkeypatch.setattr(pods_module, "get_pods", lambda client: [block_pod])
    client = SimpleNamespace(name=CLUSTER_NAME)
    common_job_parameters = {"UPDATE_TAG": TEST_UPDATE_TAG, "CLUSTER_ID": CLUSTER_ID}
    sync_storage(neo4j_session, client, TEST_UPDATE_TAG, common_job_parameters)

    # Act
    sync_pods(neo4j_session, client, TEST_UPDATE_TAG, common_job_parameters)

    # Assert
    assert {
        rel
        for rel in check_rels(
            neo4j_session,
            "KubernetesPod",
            "name",
            "KubernetesPersistentVolumeClaim",
            "name",
            "REFERENCES",
        )
        if rel[0] == "block-training-job"
    } == {("block-training-job", "block-data")}
    assert {
        rel
        for rel in check_rels(
            neo4j_session,
            "KubernetesContainer",
            "name",
            "KubernetesPersistentVolumeClaim",
            "name",
            "USES_BLOCK_DEVICE",
        )
        if rel[0] == "block-worker"
    } == {("block-worker", "block-data")}
    assert {
        rel
        for rel in check_rels(
            neo4j_session,
            "KubernetesContainer",
            "name",
            "KubernetesPersistentVolumeClaim",
            "name",
            "MOUNTS",
        )
        if rel[0] == "block-worker"
    } == set()
    container = neo4j_session.run(
        """
        MATCH (container:KubernetesContainer {name: $container_name})
              -[:USES_BLOCK_DEVICE]->
              (:KubernetesPersistentVolumeClaim {name: $claim_name})
        RETURN container.persistent_volume_claim_device_ids AS internal_claim_ids,
               container.persistent_volume_claim_devices AS device_details
        """,
        container_name="block-worker",
        claim_name="block-data",
    ).single()
    assert container is not None
    assert container["internal_claim_ids"] is None
    assert json.loads(container["device_details"]) == [
        {
            "claim_id": f"{CLUSTER_NAME}/{NAMESPACE}/block-data",
            "claim_name": "block-data",
            "device_path": "/dev/training-data",
            "volume_name": "shared-data",
        }
    ]

    # Arrange
    pod_without_device = deepcopy(block_pod)
    pod_without_device.spec.containers[0].volume_devices = []
    monkeypatch.setattr(pods_module, "get_pods", lambda client: [pod_without_device])
    next_update_tag = TEST_UPDATE_TAG + 1

    # Act
    sync_pods(
        neo4j_session,
        client,
        next_update_tag,
        {"UPDATE_TAG": next_update_tag, "CLUSTER_ID": CLUSTER_ID},
    )

    # Assert
    assert {
        rel
        for rel in check_rels(
            neo4j_session,
            "KubernetesContainer",
            "name",
            "KubernetesPersistentVolumeClaim",
            "name",
            "USES_BLOCK_DEVICE",
        )
        if rel[0] == "block-worker"
    } == set()


def test_sync_pods_cleans_up_removed_container_mount(
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
        "KubernetesContainer",
        "name",
        "KubernetesPersistentVolumeClaim",
        "name",
        "MOUNTS",
    ) == {("worker", CLAIM_NAME)}

    # Arrange
    pods_without_container_mounts = deepcopy(RAW_GPU_PODS)
    pods_without_container_mounts[0].spec.containers[0].volume_mounts = []
    monkeypatch.setattr(
        pods_module,
        "get_pods",
        lambda client: pods_without_container_mounts,
    )
    next_update_tag = TEST_UPDATE_TAG + 1

    # Act
    sync_pods(
        neo4j_session,
        client,
        next_update_tag,
        {"UPDATE_TAG": next_update_tag, "CLUSTER_ID": CLUSTER_ID},
    )

    # Assert
    assert (
        check_rels(
            neo4j_session,
            "KubernetesContainer",
            "name",
            "KubernetesPersistentVolumeClaim",
            "name",
            "MOUNTS",
        )
        == set()
    )
    assert check_rels(
        neo4j_session,
        "KubernetesPod",
        "name",
        "KubernetesPersistentVolumeClaim",
        "name",
        "REFERENCES",
    ) == {("training-job-head", CLAIM_NAME)}


@pytest.mark.parametrize(
    ("getter_name", "status"),
    (
        ("get_storage_classes", 401),
        ("get_storage_classes", 403),
        ("get_storage_classes", 500),
        ("get_persistent_volumes", 401),
        ("get_persistent_volumes", 403),
        ("get_persistent_volumes", 500),
        ("get_persistent_volume_claims", 401),
        ("get_persistent_volume_claims", 403),
        ("get_persistent_volume_claims", 500),
    ),
)
def test_sync_storage_preserves_nodes_on_api_error(
    neo4j_session,
    monkeypatch,
    _create_test_cluster,
    getter_name,
    status,
):
    # Arrange
    _mock_storage(monkeypatch)
    client = SimpleNamespace(name=CLUSTER_NAME)
    common_job_parameters = {"UPDATE_TAG": TEST_UPDATE_TAG, "CLUSTER_ID": CLUSTER_ID}
    sync_storage(neo4j_session, client, TEST_UPDATE_TAG, common_job_parameters)
    monkeypatch.setattr(
        storage_module,
        getter_name,
        lambda client: (_ for _ in ()).throw(ApiException(status=status)),
    )

    # Act
    sync_storage(
        neo4j_session,
        client,
        TEST_UPDATE_TAG + 1,
        {"UPDATE_TAG": TEST_UPDATE_TAG + 1, "CLUSTER_ID": CLUSTER_ID},
    )

    # Assert
    for label, name in (
        ("KubernetesStorageClass", STORAGE_CLASS_NAME),
        ("KubernetesPersistentVolume", VOLUME_NAME),
        ("KubernetesPersistentVolumeClaim", CLAIM_NAME),
    ):
        assert check_nodes(neo4j_session, label, ["name"]) == {(name,)}


def test_sync_storage_raises_unexpected_api_error(
    neo4j_session,
    monkeypatch,
    _create_test_cluster,
):
    monkeypatch.setattr(
        storage_module,
        "get_storage_classes",
        lambda client: (_ for _ in ()).throw(ApiException(status=400)),
    )

    with pytest.raises(ApiException):
        sync_storage(
            neo4j_session,
            SimpleNamespace(name=CLUSTER_NAME),
            TEST_UPDATE_TAG,
            {"UPDATE_TAG": TEST_UPDATE_TAG, "CLUSTER_ID": CLUSTER_ID},
        )


def test_sync_storage_preserves_nodes_on_transport_error(
    neo4j_session,
    monkeypatch,
    _create_test_cluster,
):
    _mock_storage(monkeypatch)
    client = SimpleNamespace(name=CLUSTER_NAME)
    common_job_parameters = {"UPDATE_TAG": TEST_UPDATE_TAG, "CLUSTER_ID": CLUSTER_ID}
    sync_storage(neo4j_session, client, TEST_UPDATE_TAG, common_job_parameters)
    monkeypatch.setattr(
        storage_module,
        "get_storage_classes",
        lambda client: (_ for _ in ()).throw(
            MaxRetryError(None, "/api/v1/persistentvolumes", "connection refused")
        ),
    )

    sync_storage(
        neo4j_session,
        client,
        TEST_UPDATE_TAG + 1,
        {"UPDATE_TAG": TEST_UPDATE_TAG + 1, "CLUSTER_ID": CLUSTER_ID},
    )

    assert check_nodes(
        neo4j_session,
        "KubernetesPersistentVolume",
        ["name"],
    ) == {(VOLUME_NAME,)}


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
