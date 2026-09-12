import json
from copy import deepcopy
from types import SimpleNamespace

from kubernetes.client import V1EphemeralVolumeSource
from kubernetes.client import V1PersistentVolumeClaimSpec
from kubernetes.client import V1PersistentVolumeClaimTemplate
from kubernetes.client import V1Volume
from kubernetes.client import V1VolumeDevice
from kubernetes.client import V1VolumeMount

from cartography.intel.kubernetes.pods import transform_pods
from tests.data.kubernetes.storage import RAW_GPU_PODS


def test_transform_pods_defaults_service_account_name():
    pod = SimpleNamespace(
        metadata=SimpleNamespace(
            uid="pod-1",
            name="default-sa-pod",
            namespace="my-namespace",
            creation_timestamp=None,
            deletion_timestamp=None,
            labels={},
        ),
        spec=SimpleNamespace(
            containers=[],
            volumes=[],
            node_name="node-a",
            service_account_name=None,
        ),
        status=SimpleNamespace(phase="Running", container_statuses=[]),
    )

    transformed = transform_pods([pod], "my-cluster-1")

    assert transformed == [
        {
            # A pod with no controller (no ownerReferences) resolves its
            # workload parent to its namespace; the controller ids stay None.
            "_workload_parent_deployment_id": None,
            "_workload_parent_statefulset_id": None,
            "_workload_parent_daemonset_id": None,
            "_workload_parent_job_id": None,
            "_owner_replicaset_id": None,
            "_workload_parent_namespace_name": "my-namespace",
            "uid": "pod-1",
            "name": "default-sa-pod",
            "status_phase": "Running",
            "creation_timestamp": None,
            "deletion_timestamp": None,
            "namespace": "my-namespace",
            "service_account_name": "default",
            "automount_service_account_token": None,
            "host_pid": None,
            "host_ipc": None,
            "host_network": None,
            "seccomp_profile_type": None,
            "host_path_volume_paths": [],
            "persistent_volume_claim_names": [],
            "persistent_volume_claim_ids": [],
            "service_account_id": "my-cluster-1/my-namespace/default",
            "node": "node-a",
            "node_id": "my-cluster-1/node-a",
            "architecture_normalized": None,
            "labels": "{}",
            "containers": [],
            "secret_volume_ids": [],
            "secret_env_ids": [],
        },
    ]


def test_transform_pods_maps_generic_ephemeral_volume_to_generated_claim():
    pod = deepcopy(RAW_GPU_PODS[0])
    pod.metadata.name = "ephemeral-pod"
    pod.spec.volumes = [
        V1Volume(
            name="scratch",
            ephemeral=V1EphemeralVolumeSource(
                volume_claim_template=V1PersistentVolumeClaimTemplate(
                    spec=V1PersistentVolumeClaimSpec()
                )
            ),
        )
    ]
    pod.spec.containers[0].volume_mounts = [
        V1VolumeMount(name="scratch", mount_path="/scratch")
    ]

    transformed = transform_pods([pod], "my-cluster-1")

    assert transformed[0]["persistent_volume_claim_names"] == ["ephemeral-pod-scratch"]
    assert transformed[0]["persistent_volume_claim_ids"] == [
        "my-cluster-1/my-namespace/ephemeral-pod-scratch"
    ]
    container = transformed[0]["containers"][0]
    assert container["persistent_volume_claim_ids"] == [
        "my-cluster-1/my-namespace/ephemeral-pod-scratch"
    ]
    assert container["persistent_volume_claim_read_write_ids"] == [
        "my-cluster-1/my-namespace/ephemeral-pod-scratch"
    ]
    assert json.loads(container["persistent_volume_claim_mounts"])[0]["mount_path"] == (
        "/scratch"
    )


def _owned_pod(uid: str, name: str, owner_kind: str, owner_uid: str) -> SimpleNamespace:
    return SimpleNamespace(
        metadata=SimpleNamespace(
            uid=uid,
            name=name,
            namespace="my-namespace",
            creation_timestamp=None,
            deletion_timestamp=None,
            labels={},
            owner_references=[
                SimpleNamespace(
                    kind=owner_kind,
                    uid=owner_uid,
                    name="owner",
                    api_version="apps/v1",
                    controller=True,
                ),
            ],
        ),
        spec=SimpleNamespace(
            containers=[],
            volumes=[],
            node_name="node-a",
            service_account_name="default",
        ),
        status=SimpleNamespace(phase="Running", container_statuses=[]),
    )


def test_transform_pods_collapses_replicaset_to_deployment():
    # A pod owned by a ReplicaSet resolves straight to the ReplicaSet's
    # Deployment (the ReplicaSet is collapsed out of the workload chain), and
    # the raw ReplicaSet owner is retained for the OWNED_BY edge.
    pod = _owned_pod("pod-rs", "web-pod", "ReplicaSet", "rs-uid")

    transformed = transform_pods(
        [pod], "my-cluster-1", replicaset_owner_map={"rs-uid": "dep-uid"}
    )[0]

    assert transformed["_owner_replicaset_id"] == "rs-uid"
    assert transformed["_workload_parent_deployment_id"] == "dep-uid"
    assert transformed["_workload_parent_namespace_name"] is None
    assert transformed["_workload_parent_statefulset_id"] is None


def test_transform_pods_bare_replicaset_falls_back_to_namespace():
    # A ReplicaSet with no owning Deployment is not surfaced, so the pod anchors
    # to its namespace while still recording the raw ReplicaSet owner.
    pod = _owned_pod("pod-rs2", "bare-rs-pod", "ReplicaSet", "rs-bare")

    transformed = transform_pods([pod], "my-cluster-1", replicaset_owner_map={})[0]

    assert transformed["_owner_replicaset_id"] == "rs-bare"
    assert transformed["_workload_parent_deployment_id"] is None
    assert transformed["_workload_parent_namespace_name"] == "my-namespace"


def test_transform_pods_direct_controllers():
    # StatefulSet / DaemonSet / Job owners are surfaced directly (no collapse).
    ss_pod = _owned_pod("pod-ss", "db-pod", "StatefulSet", "ss-uid")
    ds_pod = _owned_pod("pod-ds", "agent-pod", "DaemonSet", "ds-uid")
    job_pod = _owned_pod("pod-job", "job-pod", "Job", "job-uid")

    ss, ds, job = transform_pods([ss_pod, ds_pod, job_pod], "my-cluster-1")

    assert ss["_workload_parent_statefulset_id"] == "ss-uid"
    assert ss["_workload_parent_namespace_name"] is None
    assert ds["_workload_parent_daemonset_id"] == "ds-uid"
    assert job["_workload_parent_job_id"] == "job-uid"


def test_transform_pods_unavailable_workloads_fall_back_to_namespace():
    # When the workload sync was skipped (workloads_available=False), a pod owned
    # by a StatefulSet/DaemonSet/Job must anchor to its namespace rather than
    # point at a controller id that was never ingested.
    ss_pod = _owned_pod("pod-ss", "db-pod", "StatefulSet", "ss-uid")
    job_pod = _owned_pod("pod-job", "job-pod", "Job", "job-uid")

    ss, job = transform_pods(
        [ss_pod, job_pod], "my-cluster-1", workloads_available=False
    )

    for p in (ss, job):
        assert p["_workload_parent_namespace_name"] == "my-namespace"
        assert p["_workload_parent_statefulset_id"] is None
        assert p["_workload_parent_daemonset_id"] is None
        assert p["_workload_parent_job_id"] is None
        assert p["_workload_parent_deployment_id"] is None
        assert p["_owner_replicaset_id"] is None


def test_transform_pods_propagates_node_architecture_to_pod_and_container():
    pod = SimpleNamespace(
        metadata=SimpleNamespace(
            uid="pod-2",
            name="arch-pod",
            namespace="my-namespace",
            creation_timestamp=None,
            deletion_timestamp=None,
            labels={},
        ),
        spec=SimpleNamespace(
            containers=[
                SimpleNamespace(
                    name="app",
                    image="example:latest",
                    image_pull_policy="IfNotPresent",
                    resources=None,
                    env=None,
                    env_from=None,
                    volume_mounts=None,
                ),
            ],
            volumes=[],
            node_name="node-a",
            service_account_name="default",
        ),
        status=SimpleNamespace(phase="Running", container_statuses=[]),
    )

    transformed = transform_pods(
        [pod],
        "my-cluster-1",
        node_arch_map={"node-a": "arm64"},
    )

    assert transformed[0]["architecture_normalized"] == "arm64"
    assert transformed[0]["containers"][0]["image_pull_policy"] == "IfNotPresent"
    assert transformed[0]["containers"][0]["architecture_normalized"] == "arm64"


def test_transform_pods_extracts_container_ports():
    pod = SimpleNamespace(
        metadata=SimpleNamespace(
            uid="pod-3",
            name="ports-pod",
            namespace="my-namespace",
            creation_timestamp=None,
            deletion_timestamp=None,
            labels={},
        ),
        spec=SimpleNamespace(
            containers=[
                SimpleNamespace(
                    name="app",
                    image="example:latest",
                    image_pull_policy="IfNotPresent",
                    resources=None,
                    env=None,
                    env_from=None,
                    volume_mounts=None,
                    ports=[
                        SimpleNamespace(
                            container_port=8080,
                            protocol="TCP",
                            name="http",
                            host_port=None,
                        ),
                        SimpleNamespace(
                            container_port=53,
                            protocol="UDP",
                            name="dns",
                            host_port=30053,
                        ),
                        # SCTP and protocol-less ports are retained in the raw
                        # spec but excluded from the flat TCP/UDP number list.
                        SimpleNamespace(
                            container_port=9000,
                            protocol="SCTP",
                            name="sctp",
                            host_port=None,
                        ),
                    ],
                ),
            ],
            volumes=[],
            node_name="node-a",
            service_account_name="default",
        ),
        status=SimpleNamespace(phase="Running", container_statuses=[]),
    )

    transformed = transform_pods([pod], "my-cluster-1")
    container = transformed[0]["containers"][0]

    assert container["container_port_numbers"] == [53, 8080]
    assert container["host_ports"] == [30053]
    assert json.loads(container["container_ports"]) == [
        {"container_port": 8080, "protocol": "TCP", "name": "http"},
        {"container_port": 53, "protocol": "UDP", "name": "dns"},
        {"container_port": 9000, "protocol": "SCTP", "name": "sctp"},
    ]


def test_transform_pods_serializes_container_persistent_volume_claim_mounts():
    # Arrange
    pod = deepcopy(RAW_GPU_PODS[0])
    pod.spec.containers[0].volume_mounts = [
        V1VolumeMount(
            name="shared-data",
            mount_path="/data",
            read_only=False,
            sub_path="checkpoints",
        ),
        V1VolumeMount(
            name="shared-data",
            mount_path="/models",
            read_only=True,
        ),
        V1VolumeMount(name="unmatched-volume", mount_path="/ignored"),
    ]

    # Act
    transformed = transform_pods([pod], "my-cluster-1")

    # Assert
    container = transformed[0]["containers"][0]
    assert container["persistent_volume_claim_ids"] == [
        "my-cluster-1/my-namespace/shared-data"
    ]
    assert container["persistent_volume_claim_read_write_ids"] == [
        "my-cluster-1/my-namespace/shared-data"
    ]
    assert json.loads(container["persistent_volume_claim_mounts"]) == [
        {
            "claim_id": "my-cluster-1/my-namespace/shared-data",
            "claim_name": "shared-data",
            "volume_name": "shared-data",
            "mount_path": "/data",
            "mount_propagation": None,
            "read_only": False,
            "recursive_read_only": None,
            "sub_path": "checkpoints",
            "sub_path_expr": None,
        },
        {
            "claim_id": "my-cluster-1/my-namespace/shared-data",
            "claim_name": "shared-data",
            "volume_name": "shared-data",
            "mount_path": "/models",
            "mount_propagation": None,
            "read_only": True,
            "recursive_read_only": None,
            "sub_path": None,
            "sub_path_expr": None,
        },
    ]


def test_transform_pods_serializes_container_persistent_volume_claim_devices():
    # Arrange
    pod = deepcopy(RAW_GPU_PODS[0])
    pod.spec.containers[0].volume_mounts = []
    pod.spec.containers[0].volume_devices = [
        V1VolumeDevice(name="shared-data", device_path="/dev/training-data"),
        V1VolumeDevice(name="unmatched-volume", device_path="/dev/ignored"),
    ]

    # Act
    transformed = transform_pods([pod], "my-cluster-1")

    # Assert
    container = transformed[0]["containers"][0]
    assert container["persistent_volume_claim_ids"] == []
    assert container["persistent_volume_claim_read_write_ids"] == []
    assert container["persistent_volume_claim_device_ids"] == [
        "my-cluster-1/my-namespace/shared-data"
    ]
    assert json.loads(container["persistent_volume_claim_devices"]) == [
        {
            "claim_id": "my-cluster-1/my-namespace/shared-data",
            "claim_name": "shared-data",
            "device_path": "/dev/training-data",
            "volume_name": "shared-data",
        }
    ]


def test_transform_pods_excludes_read_only_claim_from_read_write_ids():
    pod = deepcopy(RAW_GPU_PODS[0])
    pod.spec.containers[0].volume_mounts = [
        V1VolumeMount(name="shared-data", mount_path="/data", read_only=True)
    ]

    container = transform_pods([pod], "my-cluster-1")[0]["containers"][0]

    assert container["persistent_volume_claim_read_write_ids"] == []
