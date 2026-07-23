import json
from types import SimpleNamespace

from cartography.intel.kubernetes.pods import transform_pods


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
